const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const fmt=(v,d=2)=>v==null?"N/A":Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const panWarning = (value) => {
  const number = Number(value);

  if (number < -50 || number > 200) {
    return `
      <span
        class="pan-alert"
        role="alert"
        title="This value is atypical and may be an error, please check your input values."
      >
        <span class="pan-alert-icon" aria-hidden="true">⚠</span>
        <span>
          This value is atypical and may be an error, please check your input values.
        </span>
      </span>
    `;
  }

  return "";
};
function showTab(id){$$('.tab,.panel').forEach(x=>x.classList.remove('active'));$(`.tab[data-tab="${id}"]`)?.classList.add('active');$(`#${id}`).classList.add('active');window.scrollTo({top:0,behavior:'smooth'})}
$$('.tab').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
function addMaterial(name='',rate=0,price=0){const tr=document.createElement('tr');tr.innerHTML=`<td><select class="m-name">${MATERIALS.map(m=>`<option ${m.name===name?'selected':''}>${m.name}</option>`).join('')}</select></td><td><input class="m-rate" type="number" min="0" step="any" value="${rate}"></td><td><input class="m-price" type="number" min="0" step="any" value="${price}"></td><td><button class="remove">Remove</button></td>`;tr.querySelector('.remove').onclick=()=>tr.remove();$('#materialRows').append(tr)}
$('#addMaterial').onclick=()=>addMaterial();addMaterial('Chicken manure - dried (4-3-2)',3500,.25);addMaterial('Composted manure (1.5-0.5-0.5)',100,0);
function addOperation(method='drill'){const d=EQUIPMENT[method];const div=document.createElement('div');div.className='operation';div.innerHTML=`<label>Method<select class="o-method">${Object.keys(EQUIPMENT).map(x=>`<option ${x===method?'selected':''}>${x}</option>`).join('')}</select></label><label>Tractor hp<input class="o-hp" type="number" value="70"></label><label>Fuel $/gal<input class="o-fuel" type="number" value="4"></label><label>Labor $/hr<input class="o-labor" type="number" value="15"></label><label>Width ft<input class="o-width" type="number" value="${d.width_ft}"></label><label>Speed mph<input class="o-speed" type="number" value="${d.speed_mph}"></label><button class="remove">Remove</button>`;div.querySelector('.o-method').onchange=e=>{const x=EQUIPMENT[e.target.value];div.querySelector('.o-width').value=x.width_ft;div.querySelector('.o-speed').value=x.speed_mph};div.querySelector('.remove').onclick=()=>div.remove();$('#operationRows').append(div)}
$('#addOperation').onclick=()=>addOperation();addOperation('drill');addOperation('rotary mow once');addOperation('disc once');addOperation('disc once');
function payload(){return{cover_crop:{area_ft2:$('#area').value,sample_lb:$('#sample').value,n_percent:$('#nPercent').value,dm_percent:$('#dmPercent').value},recommendations:{pan10:$('#recPan10').value,p2o5:$('#recP').value,k2o:$('#recK').value},materials:$$('#materialRows tr').map(r=>({name:r.querySelector('.m-name').value,rate:r.querySelector('.m-rate').value,price:r.querySelector('.m-price').value})),seed:[{cost_per_lb:$('#seed1Cost').value,rate_lb_ac:$('#seed1Rate').value},{cost_per_lb:$('#seed2Cost').value,rate_lb_ac:$('#seed2Rate').value}],inoculum_cost_ac:$('#inoculum').value,irrigations:$('#irrigations').value,irrigation_cost_ac:$('#irrigationCost').value,application_cost_ac:$('#applicationCost').value,operations:$$('.operation').map(r=>({method:r.querySelector('.o-method').value,tractor_hp:r.querySelector('.o-hp').value,fuel_price:r.querySelector('.o-fuel').value,labor_rate:r.querySelector('.o-labor').value,width_ft:r.querySelector('.o-width').value,speed_mph:r.querySelector('.o-speed').value}))}}
async function calculate(){const res=await fetch('/api/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});const data=await res.json();if(!res.ok){$('#error').textContent=data.error||'Calculation failed';$('#error').classList.remove('hidden');showTab('results');return}$('#error').classList.add('hidden');render(data);showTab('results')}
function render(d){$('#kpis').innerHTML=`<div class="kpi">Amendments<strong>$${fmt(d.total_amendment_cost)}</strong>per acre</div><div class="kpi">Cover crop management<strong>$${fmt(d.cover_crop_management_cost)}</strong>per acre</div><div class="kpi">Combined cost<strong>$${fmt(d.grand_total_cost)}</strong>per acre</div>`;const c=d.cover_crop;$('#coverResults').innerHTML=`<div class="grid four"><div>Fresh biomass<strong>${fmt(c.fresh_lb_ac)} lb/ac</strong></div><div>Dry biomass<strong>${fmt(c.dry_lb_ac)} lb/ac</strong></div><div>Total N<strong>${fmt(c.total_n_lb_ac)} lb/ac</strong></div><div>4-week PAN<strong>${fmt(c.pan4_lb_ac)} lb/ac</strong>${panWarning(c.pan4_lb_ac)}</div><div class="analysis-result"><span class="result-label">10-week PAN</span><strong class="result-value">${fmt(c.pan10_lb_ac)} lb/ac</strong>${panWarning(c.pan10_lb_ac)}</div></div>`;const labels={total_n:'Total N',dry_matter:'Dry matter',pan4:'4-week PAN',pan10:'10-week PAN',p2o5:'P₂O₅',k2o:'K₂O',ca:'Ca',mg:'Mg',s:'S',b:'B',cu:'Cu',fe:'Fe',mn:'Mn',zn:'Zn'};$('#balanceTable').innerHTML=`<thead><tr><th>Nutrient</th><th>Total applied (lb/ac)</th><th>Balance (lb/ac)</th></tr></thead><tbody>${Object.keys(labels).map(k=>`<tr><td>${labels[k]}</td><td class="output">${fmt(d.totals[k])}</td><td class="output">${fmt(d.balance[k])}</td></tr>`).join('')}</tbody>`;$('#detailTable').innerHTML=`<thead><tr><th>Material</th><th>Cost ($/ac)</th><th>Total N</th><th>10-week PAN</th><th>P₂O₅</th><th>K₂O</th></tr></thead><tbody>${d.material_details.map(x=>`<tr><td>${x.name}</td><td>${fmt(x.cost)}</td><td>${fmt(x.supplied.total_n)}</td><td>${fmt(x.supplied.pan10)}</td><td>${fmt(x.supplied.p2o5)}</td><td>${fmt(x.supplied.k2o)}</td></tr>`).join('')}</tbody>`}
$('#calculateTop').onclick=$('#calculateBottom').onclick=calculate;$("#calculateRequirements").onclick = calculate;
