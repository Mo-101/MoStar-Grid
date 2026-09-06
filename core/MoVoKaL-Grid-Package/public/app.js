const $ = id => document.getElementById(id);
const ui = Object.fromEntries(["start","start-label","end","preview","play","voice","access","access-wrap","message","composer","send","error","setup","transcript","empty","clear","call-status","connection-label","status-dot","audio","wave","hint"].map(id=>[id,$(id)]));
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition, listening = false, generation = 0, controller, audioUrl, history = [], sessionId = crypto.randomUUID();
let busy = false, audioContext, analyser, frame, locked = false;
const bars = Array.from({length:25},()=>{const bar=document.createElement("span");ui.wave.append(bar);return bar;});
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
function status(text){ui["call-status"].textContent=text;}
function error(text){ui.error.textContent=text || "";ui.error.hidden=!text;}
function headers(){return {"Content-Type":"application/json",...(locked?{Authorization:"Bearer "+ui.access.value}:{})};}
async function jsonFetch(path, options={}){
  const response=await fetch(path,{...options,headers:{...headers(),...options.headers}});
  const body=await response.json();
  if(!response.ok)throw new Error(body.error || "MoStar could not connect.");
  return body;
}
function update(){
  ui.end.hidden=!busy&&!listening&&!history.length&&!audioUrl;
  ui["start-label"].textContent=listening?"Stop listening":busy?"Interrupt & speak":"Talk to MoStar";
  ui.start.disabled=!Recognition;
  ui.preview.disabled=!ui.voice.value||busy||listening;
  ui.voice.disabled=busy||listening;
  ui.clear.disabled=!history.length;
  ui.send.disabled=!ui.message.value.trim();
}
function stopAudio(){
  ui.audio.pause();ui.audio.removeAttribute("src");ui.audio.load();
  if(audioUrl){URL.revokeObjectURL(audioUrl);audioUrl=null;}
  cancelAnimationFrame(frame);
  bars.forEach(bar=>{bar.style.height="5px";bar.style.opacity=".35";});
  ui.play.hidden=true;
}
function cancel(){
  generation++;controller?.abort();controller=null;
  if(recognition){recognition.onend=null;recognition.abort();recognition=null;}
  listening=false;busy=false;stopAudio();update();
}
function caption(role,text){
  ui.empty.hidden=true;
  const article=document.createElement("article");article.className="caption "+role;
  const speaker=document.createElement("span");speaker.className="speaker";speaker.textContent=role==="user"?"You":"MoStar";
  const p=document.createElement("p");p.textContent=text;article.append(speaker,p);ui.transcript.append(article);
  ui.transcript.scrollTop=ui.transcript.scrollHeight;
  return article;
}
function animate(){
  if(!analyser||reducedMotion.matches)return;
  const data=new Uint8Array(analyser.frequencyBinCount);
  const draw=()=>{
    analyser.getByteFrequencyData(data);
    bars.forEach((bar,i)=>{const level=data[Math.floor(i*data.length/50)]/255;bar.style.height=(5+level*40)+"px";bar.style.opacity=String(.35+level*.65);});
    if(!ui.audio.paused)frame=requestAnimationFrame(draw);
  };draw();
}
async function play(){
  try{
    if(!audioContext){
      audioContext=new AudioContext();analyser=audioContext.createAnalyser();analyser.fftSize=256;
      const source=audioContext.createMediaElementSource(ui.audio);source.connect(analyser);analyser.connect(audioContext.destination);
    }
    await audioContext.resume();await ui.audio.play();ui.play.hidden=true;animate();status("MoStar is speaking. You can interrupt.");
  }catch{ui.play.hidden=false;status("Your reply is ready. Tap Enable audio to listen.");}
}
async function speak(text,turn,signal){
  if(!ui.voice.value)throw new Error("No voice model is available. The reply is in your captions.");
  const response=await fetch("/api/speak",{method:"POST",headers:headers(),body:JSON.stringify({text,voice:ui.voice.value}),signal});
  if(!response.ok){const data=await response.json();throw new Error(data.error);}
  const blob=await response.blob();
  if(turn!==generation)return;
  audioUrl=URL.createObjectURL(blob);ui.audio.src=audioUrl;await play();
}
ui.audio.addEventListener("ended",()=>{stopAudio();busy=false;status("Your turn. Take your time.");update();});
ui.audio.addEventListener("error",()=>{if(audioUrl){stopAudio();busy=false;error("The audio could not play. Your reply is still in the captions.");update();}});
ui.play.addEventListener("click",play);
ui.message.addEventListener("input",update);
ui.start.addEventListener("click",()=>{
  if(listening){recognition?.stop();return;}
  cancel();error("");
  if(!Recognition)return;
  recognition=new Recognition();recognition.lang=navigator.language||"en-US";
  recognition.continuous=true;recognition.interimResults=true;
  const prefix=ui.message.value.trim();
  recognition.onresult=event=>{
    let words="";
    for(let i=0;i<event.results.length;i++)words+=event.results[i][0].transcript+" ";
    ui.message.value=(prefix+" "+words).trim().slice(0,4000);update();
  };
  recognition.onerror=event=>{
    listening=false;
    error(event.error==="not-allowed"?"Microphone permission was denied. Allow it in your browser, or type your message.":event.error==="no-speech"?"I didn’t catch that. Try again, or type your message.":"Speech recognition stopped. You can still type your message.");
    update();
  };
  recognition.onend=()=>{listening=false;status("Edit your words if needed, then press Send.");update();};
  try{recognition.start();listening=true;status("Listening. Pause freely — Send when you’re ready.");update();}
  catch{error("Couldn’t start the microphone. Try again or type your message.");}
});
ui.composer.addEventListener("submit",async event=>{
  event.preventDefault();
  const text=ui.message.value.trim();if(!text)return;
  cancel();error("");const turn=generation;controller=new AbortController();busy=true;
  const previous=history.slice(-12);
  caption("user",text);history.push({role:"user",content:text});ui.message.value="";status("MoStar is thinking it through…");update();
  try{
    const data=await jsonFetch("/api/turn",{method:"POST",body:JSON.stringify({text,history:previous,sessionId}),signal:controller.signal});
    if(turn!==generation)return;
    const article=caption("assistant",data.text);
    history.push({role:"assistant",content:data.text});history=history.slice(-12);
    if(!data.semanticAvailable||data.semanticSource!=="llm"){
      const note=document.createElement("small");note.textContent=data.semanticAvailable?"Semantic cues used Grid’s fallback analysis.":"Semantic context unavailable for this turn.";article.append(note);
    }
    status("Giving the words a voice…");update();
    await speak(data.text,turn,controller.signal);
  }catch(cause){if(turn!==generation)return;busy=false;error(cause.message);status("Let’s try that again when you’re ready.");update();}
});
ui.preview.addEventListener("click",async()=>{
  cancel();error("");const turn=generation;controller=new AbortController();busy=true;update();status("Preparing a voice sample…");
  try{
    let sample=ui.message.value.trim();
    if(!sample){
      const data=await jsonFetch("/api/turn",{method:"POST",body:JSON.stringify({text:"Introduce your voice naturally in one complete sentence.",history:[],sessionId}),signal:controller.signal});
      sample=data.text;
    }
    if(turn!==generation)return;
    caption("assistant",sample);
    await speak(sample,turn,controller.signal);
  }
  catch(cause){if(turn!==generation)return;busy=false;error(cause.message);status("Voice preview unavailable.");update();}
});
function reset(){cancel();history=[];sessionId=crypto.randomUUID();ui.transcript.querySelectorAll(".caption").forEach(node=>node.remove());ui.empty.hidden=false;ui.message.value="";error("");status("A fresh conversation. Make yourself comfortable.");update();}
ui.end.addEventListener("click",reset);ui.clear.addEventListener("click",reset);
ui.access.addEventListener("change",check);
async function check(){
  try{
    const config=await jsonFetch("/api/config");locked=config.locked;ui["access-wrap"].hidden=!locked;
    if(locked&&!ui.access.value){status("Enter your access key below to connect.");update();return;}
    const data=await jsonFetch("/api/status");
    ui.voice.replaceChildren();
    for(const voice of data.voices){const option=document.createElement("option");option.value=voice.id;option.textContent=voice.label;ui.voice.append(option);}
    if(data.voices.some(v=>v.id===data.defaultVoice))ui.voice.value=data.defaultVoice;
    ui["connection-label"].textContent=data.voiceReady?"MOSTAR VOICE CONNECTED":"VOICE SERVICE OFFLINE";
    ui["status-dot"].classList.toggle("connected",data.voiceReady);
    ui.setup.hidden=data.voiceReady&&data.gridReachable;
    if(!data.gridReachable)error("MoStar Voice is available, but Grid health could not be verified. You can preview the voice; conversation needs a ready Grid mind.");
    else if(!data.voiceReady)error("MoStar Voice is offline. Start the voice service, then reload this page.");
    status(data.voiceReady?"Make yourself comfortable.":"Waiting for MoStar Voice.");
  }catch(cause){error(cause.message);status("Connection needs attention.");}
  if(!Recognition)ui.hint.textContent="This browser has no speech recognition. Type below, or use a browser that supports it.";
  update();
}
window.addEventListener("pagehide",cancel);
check();
