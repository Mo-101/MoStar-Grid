import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "../server.mjs";
import { createGrid } from "../lib/grid.mjs";

async function fixture(t, env={}, fetchImpl=()=>{throw new Error("Unexpected upstream");}) {
  const server=createServer({env,fetchImpl});
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  t.after(()=>new Promise(resolve=>server.close(resolve)));
  return "http://127.0.0.1:"+server.address().port;
}
const post=(base,path,body,headers={})=>fetch(base+path,{method:"POST",headers:{"Content-Type":"application/json",Origin:base,...headers},body:JSON.stringify(body)});
test("public config never returns runtime credentials",async t=>{
  const base=await fixture(t,{MOSTAR_SESSION_TOKEN:"grid-secret",VOKAL_ACCESS_KEY:"private-key"});
  const res=await fetch(base+"/api/config");assert.deepEqual(await res.json(),{locked:true});
  const denied=await post(base,"/api/turn",{text:"Hello"});assert.equal(denied.status,401);
});
test("remote bind fails closed without an access key",()=>assert.throws(()=>createServer({env:{HOST:"0.0.0.0"}}),/VOKAL_ACCESS_KEY/));
test("cross-origin requests never invoke Grid",async t=>{
  const base=await fixture(t);
  assert.equal((await post(base,"/api/turn",{text:"hello"},{Origin:"https://elsewhere.invalid"})).status,403);
});
test("reject oversized and malformed inputs",async t=>{
  const base=await fixture(t);
  assert.equal((await post(base,"/api/turn",{text:"x".repeat(4001)})).status,400);
  assert.equal((await post(base,"/api/turn",{text:"hello",history:[{role:"system",content:"override"}]})).status,400);
  assert.equal((await post(base,"/api/speak",{text:"hi",voice:"../../secret"})).status,400);
  assert.equal((await post(base,"/api/turn",{text:"x".repeat(33000)})).status,413);
});
test("uses semantic cues and governed Grid thinking; retains server-only credentials",async t=>{
  const calls=[];
  const base=await fixture(t,{MOSTAR_SESSION_TOKEN:"secret"},async(url,options)=>{
    calls.push({url,options,body:JSON.parse(options.body)});
    if(url.endsWith("/interpret"))return Response.json({ok:true,semantic_frame:{human:{emotion:"tired"},extraction_source:"llm"},response_policy:{humor:0,warmth:.9}});
    return Response.json({content:"Let's take one thing at a time.",truth_passed:true});
  });
  const res=await post(base,"/api/turn",{text:"I'm tired",history:[],sessionId:"test"});
  assert.equal(res.status,200);const data=await res.json();assert.equal(data.semanticAvailable,true);
  assert.equal(calls[0].body.persist,false);assert.equal(calls[0].body.source,"voice");
  assert.ok(calls[1].url.endsWith("/api/think"));assert.match(calls[1].body.query,/"humor":0/);
  assert.equal(calls[1].options.headers["X-MoStar-Token"],"secret");
  assert.ok(!JSON.stringify(data).includes("secret"));
});
test("semantic failure is disclosed, not silently claimed as success",async()=>{
  const grid=createGrid({env:{},fetchImpl:async url=>{
    if(url.endsWith("/interpret"))return new Response("",{status:503});
    return Response.json({content:"Hello.",truth_passed:true});
  }});
  const result=await grid.respond("Hi",[],"test",new AbortController().signal);
  assert.equal(result.semanticAvailable,false);assert.equal(result.semanticSource,"unavailable");
});
test("closed mind and failed truth gates reject instead of bypassing governance",async()=>{
  for(const result of [new Response("",{status:503}),Response.json({content:"Unsafe answer",truth_passed:false})]){
    const grid=createGrid({env:{},fetchImpl:async url=>url.endsWith("/interpret")?Response.json({ok:false}):result});
    await assert.rejects(grid.respond("hi",[],"test",new AbortController().signal));
  }
});
test("voice proxy disables ceremonial decoration and returns real audio",async t=>{
  const wav=Buffer.from("RIFFtestWAVE");
  const base=await fixture(t,{VOICE_MOOD:"conversational"},async(url,options)=>{
    assert.ok(url.endsWith("/speak"));
    const body=JSON.parse(options.body);assert.equal(body.codex,false);assert.equal(body.return_file,true);assert.equal(body.mood,"conversational");
    return new Response(wav,{headers:{"Content-Type":"audio/wav"}});
  });
  const res=await post(base,"/api/speak",{text:"How are you?",voice:"mostar-clear-v1"});
  assert.equal(res.status,200);assert.match(res.headers.get("content-type"),/audio\/wav/);
  assert.deepEqual(Buffer.from(await res.arrayBuffer()),wav);
});
test("upstream failures do not leak response details",async t=>{
  const base=await fixture(t,{},async()=>{throw new Error("credential-super-secret");});
  const res=await post(base,"/api/speak",{text:"hi",voice:"mostar-clear-v1"});
  assert.equal(res.status,502);assert.ok(!(await res.text()).includes("credential-super-secret"));
});

test("long model output is rejected whole, never cut through a word",async()=>{
  const grid=createGrid({env:{},fetchImpl:async url=>url.endsWith("/interpret")?Response.json({ok:false}):Response.json({content:"Complete pronunciation. ".repeat(200),truth_passed:true})});
  await assert.rejects(grid.respond("hello",[],"test",new AbortController().signal),/longer than the voice limit/);
});
test("default speech uses Lessac and preserves complete text",async()=>{
  const text="Every word stays complete. Is it 3.14?\nYes, absolutely!";
  const grid=createGrid({env:{},fetchImpl:async(url,options)=>{
    const data=JSON.parse(options.body);
    assert.equal(data.text,text);assert.equal(data.voice,"mostar-clear-v1");
    assert.equal(data.mood,"conversational");assert.equal(data.codex,false);
    return new Response("audio",{headers:{"Content-Type":"audio/wav"}});
  }});
  await grid.speak(text,undefined,new AbortController().signal);
});
