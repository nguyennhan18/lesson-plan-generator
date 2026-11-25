import {defineConfig} from '@playwright/test';
import fs from 'node:fs';
const port=Number(process.env.LESSONAI_TEST_PORT||8000);
if(!Number.isInteger(port)||port<1024||port>65535)throw new Error('Invalid LESSONAI_TEST_PORT');
const baseURL=`http://127.0.0.1:${port}`;
const localChrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
export default defineConfig({
  testDir:'./e2e',timeout:45000,workers:1,fullyParallel:false,
  reporter:[['list'],['html',{outputFolder:'playwright-report',open:'never'}]],
  use:{baseURL,viewport:{width:1440,height:1000},trace:'retain-on-failure',screenshot:'only-on-failure',launchOptions:fs.existsSync(localChrome)?{executablePath:localChrome}:{}},
  webServer:{command:`LESSONAI_LOCAL_ORIGINS=${baseURL} GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= ${process.env.LESSONAI_TEST_PYTHON||'../backend/venv/bin/python'} -m uvicorn lessonai.main:app --app-dir ../backend/src --host 127.0.0.1 --port ${port}`,url:`${baseURL}/api/v1/health`,reuseExistingServer:false,timeout:30000},
});
