// EFL shared browser helpers, loaded on every page.
function showMessage(id, text) {                                        
  document.getElementById(id).textContent = text;                       
}                                                                       

function formatMoney(value, code) {                                     
  return Number(value).toLocaleString("en-GB", { style: "currency", currency: code, currencyDisplay: "narrowSymbol", minimumFractionDigits: 2, maximumFractionDigits: 2 });  
}                                                                       

async function postJson(url, body) {                                    
  const response = await fetch(url, {                                   
    method: "POST",                                                    
    headers: { "Content-Type": "application/json" },                    
    body: JSON.stringify(body),                                         
  });                                                                   
  if (response.status === 401) {                                        
    window.location.href = "/login";                                    
  }                                                                     
  const data = await response.json();                                   
  return { ok: response.ok, status: response.status, data: data };      
}                                                                       

function cacheForm(name, values) {                                      
  try {                                                                 
    localStorage.setItem("efl-" + name, JSON.stringify(values));        
  } catch (problem) {                                                   
    console.warn("Could not cache the form", problem);                  
  }                                                                     
}                                                                       

function restoreForm(name) {                                            
  try {                                                                 
    const text = localStorage.getItem("efl-" + name);                   
    return text ? JSON.parse(text) : null;                              // Turn it back into an object, or null if nothing is stored
  } catch (problem) {                                                   
    return null;                                                        
  }                                                                     
}                                                                       

function clearCachedForm(name) {                                        
  try {                                                                 
    localStorage.removeItem("efl-" + name);                             
  } catch (problem) {                                                   
    console.warn("Could not clear the cache", problem);                 
  }                                                                     
}                                                                       