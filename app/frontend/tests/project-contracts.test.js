import assert from 'node:assert/strict';
import {test} from 'node:test';
import {normalizeDeck,mutateDeck} from '../src/shared/storage/projectStore.js';

test('migration preserves unknown content and metadata and rejects alias conflicts',()=>{
  const deck=normalizeDeck({slides:[{slide_number:3,title:'A',blocks:[{type:'table',rows:[[1,2]]}],source_refs:[{source:'book',slide_id:'page1',page:1}]}]});
  assert.equal(deck.slides[0].slide_index,1);assert.equal(deck.slides[0].source_refs[0].id,'page1');assert.equal(deck.slides[0].source_refs[0].page,1);
  assert.deepEqual(deck.slides[0].blocks,[{type:'table',rows:[[1,2]]}]);
  assert.throws(()=>normalizeDeck({slides:[{slide_number:1,slide_index:2}]}));
});

test('reorder preserves identity and annotations; edits invalidate only their images and review',()=>{
  const deck=normalizeDeck({slides:[{title:'A',chart_image_base64:'imageA',chart_spec:{requirement_token:'old'}},{title:'B',chart_image_base64:'imageB'}]});
  deck.annotations={[deck.slides[0].slide_id]:[{id:'stroke'}]};deck.review_token='review';
  const reordered=mutateDeck(deck,{...deck,slides:[deck.slides[1],deck.slides[0]]});
  assert.equal(reordered.slides[1].slide_id,deck.slides[0].slide_id);assert.deepEqual(reordered.annotations,deck.annotations);assert.equal(reordered.revision,1);
  const changed=mutateDeck(reordered,{...reordered,slides:reordered.slides.map((s,i)=>i?{...s,title:'A changed'}:s)});
  assert.equal(changed.slides[0].chart_image_base64,'imageB');assert.equal(changed.slides[1].chart_image_base64,undefined);assert.equal(changed.slides[1].chart_spec.requirement_token,undefined);assert.equal(changed.review_token,undefined);
  assert.equal(deck.slides[0].title,'A');
});

test('new confirmations survive their own save; changing a question resets only its poll',()=>{
  const deck=normalizeDeck({slides:[{title:'A',question:'Question',quiz_options:[],chart_spec:{expression:'x'}}]});
  const sid=deck.slides[0].slide_id;deck.polls={[sid]:{A:3},other:{B:2}};
  const confirmed=mutateDeck(deck,{...deck,slides:[{...deck.slides[0],chart_spec:{expression:'x',requirement_token:'confirmed'}}]});
  assert.equal(confirmed.slides[0].chart_spec.requirement_token,'confirmed');
  const edited=mutateDeck(confirmed,{...confirmed,slides:[{...confirmed.slides[0],question:'Changed'}]});
  assert.equal(edited.polls[sid],undefined);assert.deepEqual(edited.polls.other,{B:2});
});

test('lesson review is invalidated by content edits while provenance survives JSON backup',async()=>{
  const {mutatePlan}=await import('../src/shared/storage/projectStore.js');
  const plan={lesson_title:'Bài cũ',activities:[],generation_metadata:{provider:'google',model:'test-model',prompt_sha256:'a'.repeat(64)},approved_outline:{outline_slides:[{id:'one'}]},review_token:'signed',quality_report:{status:'ready'}};
  const roundtrip=JSON.parse(JSON.stringify(plan));
  assert.deepEqual(roundtrip,plan);
  assert.equal(mutatePlan(plan,{...plan,quality_report:{status:'needs_review'}}).review_token,'signed');
  const edited=mutatePlan(plan,{...plan,lesson_title:'Bài đã sửa'});
  assert.equal(edited.review_token,undefined);assert.equal(edited.quality_report,undefined);
  assert.deepEqual(edited.generation_metadata,plan.generation_metadata);
  assert.deepEqual(edited.approved_outline,plan.approved_outline);
  assert.equal(plan.review_token,'signed');
});
