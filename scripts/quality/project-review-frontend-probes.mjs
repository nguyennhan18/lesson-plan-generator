// Local audit only. Baseline records findings; acceptance enforces M0 containment.
// node scripts/quality/project-review-frontend-probes.mjs --input /tmp/backend.json --output /tmp/frontend.json
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runInNewContext } from 'node:vm';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: {
  input: { type: 'string' }, output: { type: 'string' },
  mode: { type: 'string', default: 'baseline' }, help: { type: 'boolean' }
} });
if (values.help) {
  console.log('Usage: node scripts/quality/project-review-frontend-probes.mjs --input backend.json --output new-frontend.json [--mode baseline|acceptance]');
  process.exit(0);
}
if (!values.input || !values.output || !['baseline', 'acceptance'].includes(values.mode)) {
  throw new Error('--input, --output and a valid --mode are required');
}
if (fs.existsSync(values.output)) throw new Error(`Evidence already exists: ${values.output}`);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const read = relative => fs.readFileSync(path.join(root, relative), 'utf8');
function anchored(source, pattern, label) {
  const found = source.match(pattern)?.[0];
  if (!found) throw new Error(`Audit anchor missing: ${label}`);
  return found;
}
const evidence = JSON.parse(fs.readFileSync(values.input, 'utf8'));
const plotter = read('app/frontend/src/shared/math/FunctionPlotter.jsx');
const usesDynamicFunction = /new\s+Function\s*\(/.test(plotter);
let markerSet = false;
const expressions = {};
if (usesDynamicFunction) {
  // Execute only the reviewed transformation in an isolated VM with a fixed,
  // non-destructive marker payload. Never execute a file-provided expression.
  const transformSource = anchored(plotter, /const evalExpr = expr[\s\S]*?(?=const fn = new Function\('x')/, 'legacy plot transformation');
  const sandbox = {};
  const source = `${transformSource}\nreturn evalExpr;`;
  const transform = runInNewContext(`(expr) => { ${source} }`, sandbox, { timeout: 1000 });
  markerSet = runInNewContext(`((x) => (${transform('(globalThis.lessonReviewMarker = 731, x)')}))(2); globalThis.lessonReviewMarker === 731`, sandbox, { timeout: 1000 });
  for (const expression of ['log(x)', 'exp(x)', 'Abs(x)']) {
    try {
      runInNewContext(`((x) => (${transform(expression)}))(2)`, {}, { timeout: 1000 });
      expressions[expression] = 'accepted';
    } catch (error) { expressions[expression] = error.name; }
  }
} else {
  anchored(plotter, /export default function FunctionPlotter/, 'FunctionPlotter component');
}
evidence.frontend_expression_evaluation = {
  uses_dynamic_function: usesDynamicFunction, marker_set: markerSet,
  supported_backend_functions_failing_in_frontend: expressions,
  temporarily_unavailable: plotter.includes('temporarily_unavailable')
};

const analytics = read('app/frontend/src/features/analytics/AnalyticsScreen.jsx');
const analyticsSource = anchored(analytics, /const total = data\.total_students[\s\S]*?const countStandard = [^;]+;/, 'analytics calculations');
const uiCalculation = runInNewContext(`(() => { ${analyticsSource}\nreturn {rateBelow5, rateAbove8, countBelow5, countAbove8, countStandard}; })()`, { data: evidence.analytics_api_response }, { timeout: 1000 });
evidence.frontend_analytics = {
  api_total_students: evidence.analytics_api_response.total_students,
  api_rate_below_5: evidence.analytics_api_response.rate_below_5,
  api_rate_above_8: evidence.analytics_api_response.rate_above_8,
  actual_students_below_5: 2, actual_students_above_or_equal_8: 2,
  ui_calculation: uiCalculation,
  cv_displayed_as_percent_without_scaling: evidence.analytics_api_response.cv
};

const actions = read('app/frontend/src/features/generation/lessonGenerationActions.js');
const outlineSource = anchored(actions, /const handleGenerateFromOutline[\s\S]*?(?=\/\/ ================= HÀM GỌI AI)/, 'generation outline action');
const schema = anchored(read('app/backend/src/lessonai/schemas/slide_schema.py'), /class SlideDeckSchema[\s\S]+/, 'SlideDeckSchema');
const poll = anchored(read('app/frontend/src/features/presentation/InteractiveQuizCard.jsx'), /votes = \{[^}]+\}/, 'initial poll votes');
const teacherChat = read('app/frontend/src/features/chat/TeacherChatDock.jsx');
evidence.frontend_contracts = {
  approved_outline_slides_transmitted: outlineSource.includes('outline_slides'),
  final_slide_count_transmitted: outlineSource.includes('num_slides'),
  fixed_teacher_session_id: teacherChat.includes("session_id: 'session_teacher_dock'"),
  global_math_color_override: read('app/frontend/src/styles/index.css').includes('color: #141414 !important;'),
  initial_poll_votes: poll,
  generated_deck_id_in_schema: /\n\s+(?:id|deck_id)\s*:/.test(schema)
};
evidence.frontend_m0_checks = {
  no_dynamic_expression_execution: !usesDynamicFunction && !markerSet && !/\beval\s*\(/.test(plotter)
};
evidence.mode = values.mode;
fs.mkdirSync(path.dirname(path.resolve(values.output)), { recursive: true });
fs.writeFileSync(values.output, JSON.stringify(evidence, null, 2), { flag: 'wx' });
console.log(JSON.stringify({ frontend_expression_evaluation: evidence.frontend_expression_evaluation, frontend_analytics: evidence.frontend_analytics, frontend_contracts: evidence.frontend_contracts, frontend_m0_checks: evidence.frontend_m0_checks }, null, 2));
if (values.mode === 'acceptance' && (!Object.values(evidence.frontend_m0_checks).every(Boolean)
  || !Object.values(evidence.m0_checks ?? { missing_backend_checks: false }).every(Boolean))) process.exitCode = 1;
