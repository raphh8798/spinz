import "../App.css";
import {useState, useEffect} from "react";
import * as api from "../api";

export default function Actors() {
  const [data, setData] = useState({ watched_actors: [], performs: [] });
  const [actorName, setActorName] = useState("");
  const [year, setYear] = useState("");
  const [page, setPage] = useState(1);

  const years = [...new Set(data.performs.map(p => p.styear))].sort();
  const filtered = year ? data.performs.filter(p => p.styear === year) : data.performs;

  const PAGE_SIZE = 10;
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => {
    api.getActors().then(setData);
  }, []);


  function handleDeleteActor(actorId) {
    const actor = data.watched_actors.find(a => a.id === actorId);
    if(!window.confirm(`'${actor.actor_name}' 배우를 정말 삭제하시겠습니까?`)) return;
    api.deleteActor(actorId).then(setData);
  }

  
  function handleAddActor(e) {
    e.preventDefault();
    if(actorName.trim() === "") {
      alert("배우 이름을 입력하세요!");
      return;
    }else if(confirm(`'${actorName}' 배우를 추가하시겠습니까?`)) {
      api.addActor(actorName).then(setData);
      setActorName(""); // 입력 필드 초기화
    }
  }


  return (
    <div className="card">
      <h2>관심 배우 목록</h2>
      {data.watched_actors.map(actor => (
        <div className="item-card" key={actor.id}>
          <span>{actor.actor_name}</span>
          <button className="s-btn" onClick={() => handleDeleteActor(actor.id)}>삭제</button>
        </div>
      ))}

      <h2>배우 추가</h2>
      <form onSubmit={handleAddActor}>
        <input type="text" name="actorName" placeholder="배우 이름"
               value={actorName} onChange={(e) => setActorName(e.target.value)} />
        <button className="s-btn" type="submit">추가</button>
      </form>

      <h2>출연작</h2>
      <label>연도: </label>
      <select value={year} onChange={(e) => { setYear(e.target.value); setPage(1); }}>
        <option value="">전체</option>
        {years.map(y => <option key={y} value={y}>{y}</option>)}
      </select>
      {
        data.performs.length === 0 ?
          <p>배우를 추가하면 여기에 표시됩니다.</p> :
          filtered.length === 0 ?
            <p>선택한 연도에 해당하는 출연작이 없습니다.</p> :
            paged.map(p => (
              <div className="item-card" key={p.mt20id} style={{ display: "block" }}>
                {p.prfnm} ({p.prfpdfrom}~{p.prfpdto}) : {p.fcltynm}<br/>
                ▶ {p.prfcast}
              </div>
            ))
      }
      {totalPages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", gap: "8px", marginTop: "12px" }}>
          <button className="s-btn" disabled={page === 1} onClick={() => setPage(page - 1)}>이전</button>
          <span>{page} / {totalPages}</span>
          <button className="s-btn" disabled={page === totalPages} onClick={() => setPage(page + 1)}>다음</button>
        </div>
      )}
    </div>
  );
}
