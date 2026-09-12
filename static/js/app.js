// SchedHub v3 — Global JS

function toggleSidebar(){
  document.getElementById('sidebar').classList.toggle('open');
}

document.addEventListener('click',function(e){
  const sb=document.getElementById('sidebar');
  const tb=document.querySelector('.sidebar-toggle');
  if(sb&&tb&&!sb.contains(e.target)&&!tb.contains(e.target)){
    sb.classList.remove('open');
  }
});

function showToast(msg, type='success'){
  const el=document.createElement('div');
  el.className=`toast-el toast-${type}`;
  const icon={success:'check-circle',danger:'times-circle',warning:'exclamation-circle'}[type]||'info-circle';
  el.innerHTML=`<i class="fas fa-${icon}"></i> ${msg}`;
  document.body.appendChild(el);
  setTimeout(()=>{ el.style.opacity='0'; el.style.transition='opacity .3s'; setTimeout(()=>el.remove(),300); },2800);
}
