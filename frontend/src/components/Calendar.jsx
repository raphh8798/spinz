import "../App.css";

import { useState, useEffect } from "react";
import * as api from "../api.js";

export default function Calendar() {
  const [data, setData] = useState(null);
  const [month, setMonth] = useState(undefined);
  const [selectedDate , setSelectedDate] = useState(null);
  const [isPerformToggleOn, setIsPerformToggleOn] = useState(false);
  const [isActorToggleOn, setIsActorToggleOn] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.getCalendar(month).then((data) => {
      setData(data);
      setMonth(`${data.year}-${String(data.month).padStart(2, "0")}`);
    });
  }, [month]);

  if (!data) {
    return <p>로딩 중...</p>;
  }

  // 이번 달 1일이 무슨 요일인지(0=일 ~ 6=토)
  const firstDay = new Date(data.year, data.month - 1, 1).getDay();
  // 이번 달이 며칠까지 있는지((다음 달 0일 = 이번 달 마지막 날)
  const lastDate = new Date(data.year, data.month, 0).getDate();
  // 1부터 그 마지막 날짜까지 배열
  const allDates = Array.from({ length: lastDate }, (_, i) => i + 1);

  function getFilteredPerforms(dateStr) {
    const performs = data.by_date[dateStr] || [];
    if (!isPerformToggleOn && !isActorToggleOn) return performs;
    return performs.filter(p =>
      (isPerformToggleOn && p.is_fav) ||
      (isActorToggleOn && p.actor_name.length > 0)
    );
  }


  return (
    <div className="card">
      <div className="cal-header">
        <button className="s-btn" onClick={() => { setMonth(data.prev_month); setSelectedDate(null); }}>◀</button>
        <h3 className="cal-month">{data.year}년 {data.month}월</h3>
        <button className="s-btn" onClick={() => { setMonth(data.next_month); setSelectedDate(null); }}>▶</button>
      </div>
      <button onClick={() => { setMonth(undefined); setSelectedDate(null); }}>🔄️ 이번 달로 돌아가기</button>

      <div className="toggle-container">
        <h5>찜한 공연</h5>
        <div onClick={() => setIsPerformToggleOn(!isPerformToggleOn)}>
          <div className={`toggle-perform ${isPerformToggleOn ? 'on' : 'off'}`} />
        </div>
        <h5>관심 배우</h5>
        <div onClick={() => setIsActorToggleOn(!isActorToggleOn)}>
          <div className={`toggle-actor ${isActorToggleOn ? 'on' : 'off'}`} />
        </div>
      </div>

      <div className="cal">
        <div className="cal-day-label">일</div>
        <div className="cal-day-label">월</div>
        <div className="cal-day-label">화</div>
        <div className="cal-day-label">수</div>
        <div className="cal-day-label">목</div>
        <div className="cal-day-label">금</div>
        <div className="cal-day-label">토</div>
        
        {Array.from({ length: firstDay }, (_, i) => (
          <div key={`empty-${i}`}></div> /* 빈 칸 채우기 */
        ))}

        {allDates.map((date) => {
          const dateStr = `${data.year}-${String(data.month).padStart(2, "0")}-${String(date).padStart(2, "0")}`;
          const filtered = getFilteredPerforms(dateStr);
          const hasFav = isPerformToggleOn && filtered.some(p => p.is_fav);
          const hasActorMatch = isActorToggleOn && filtered.some(p => p.actor_name.length > 0);

          return (
            <div key={date} className="cal-box" onClick={() => { setSelectedDate(dateStr); setPage(1); }}>
              {date}
              <span className="cal-marks">
                {filtered.length > 0 && !isPerformToggleOn && !isActorToggleOn && <span style={{color: "#ff3d3d"}}>⋮</span>}
                {hasFav && <span>💌</span>}
                {hasActorMatch && <span>💟</span>}
              </span>
            </div>
          );
        })}
      </div>
      
      {selectedDate && (() => {
        const dayPerforms = getFilteredPerforms(selectedDate);
        const PAGE_SIZE = 10;
        const totalPages = Math.ceil(dayPerforms.length / PAGE_SIZE);
        const paged = dayPerforms.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

        return (
          <div className="list-container">
            <h3>{selectedDate} 공연 목록</h3>
            {paged.map((s) => (
              /* 선택된 날짜에 대한 공연 목록 표시 - 토글 기능 포함 */
              <div className="item-card" key={s.mt20id}>
                <span>{s.prfnm} {s.actor_name.join(", ")}</span>
                <button className="s-btn" onClick={() => api.toggleFavorite(s.mt20id, month).then(setData)}>
                  {s.is_fav ? "💌" : "♡"}
                </button>
              </div>
            ))}
            {totalPages > 1 && (
              <div style={{ display: "flex", justifyContent: "center", gap: "8px", marginTop: "12px" }}>
                <button className="s-btn" disabled={page === 1} onClick={() => setPage(page - 1)}>이전</button>
                <span>{page} / {totalPages}</span>
                <button className="s-btn" disabled={page === totalPages} onClick={() => setPage(page + 1)}>다음</button>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}
