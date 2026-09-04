// Flask API 호출 공용 함수 - 컴포넌트에서 import해서 씀
// fetch(url, { credentials: "include", ... }) 로 세션 쿠키 같이 보내기 (필수 - 이거 빠지면 로그인 세션 유지 안 됨)
// 응답은 await res.json()으로 파싱해서 리턴

const BASE = "/api";


export async function login(name, password) {
// Flask가 request.form.get("name")으로 읽으니 JSON 아니라 form-urlencoded로 보내야 함
  return await fetch(`${BASE}/login`, 
               { method: "POST",
                 credentials: "include",
                 headers: { "Content-Type": "application/x-www-form-urlencoded" },
                 body: new URLSearchParams({ name, password })
               })
              .then(res => res.json())
}


export async function logout() {
  return await fetch(`${BASE}/logout`, { method: "POST", credentials: "include" })
              .then(res => res.json());
}


export async function getMe() {
  return await fetch(`${BASE}/me`, { method: "GET", credentials: "include" })
              .then(res => res.ok ? res.json() : null);
}


export async function getCalendar(month) {
  if(!month){
    var now = new Date();
    month = `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, '0')}`;
  }
  return await fetch(`${BASE}/calendar?month=${month}`, { method: "GET", credentials: "include" })
              .then(res => res.json());
}


export async function toggleFavorite(mt20id, month) {
  return await fetch(`${BASE}/favorite/${mt20id}?month=${month}`, { method: "POST", credentials: "include" })
              .then(res => res.json());
}


export async function getActors() {
  return await fetch(`${BASE}/actors`, { method: "GET", credentials: "include" })
              .then(res => res.json());
}


export async function addActor(actorName) {
  return await fetch(`${BASE}/actors`,
               { method: "POST",
                 credentials: "include",
                 headers: { "Content-Type": "application/x-www-form-urlencoded" },
                 body: new URLSearchParams({ actor_name: actorName })
               })
              .then(res => res.json());
}


export async function deleteActor(actorId) {
  return await fetch(`${BASE}/actors/${actorId}/delete`, { method: "POST", credentials: "include" })
              .then(res => res.json());
}
