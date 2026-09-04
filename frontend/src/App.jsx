import {useState, useEffect} from "react";
import Login from "./components/Login";
import Calendar from "./components/Calendar";
import Actors from "./components/Actors";
import * as api from "./api.js";

function App() {
  const [userName, setUserName] = useState(null);
  const [page, setPage] = useState("calendar");
  const [checked, setChecked] = useState(false);   // 세션 확인

  useEffect(() => {
    api.getMe().then((data) => {
      if (data) setUserName(data.user_name);
      setChecked(true);
    });
  }, []);

  if (!checked) {
    return <p>로딩 중...</p>;
  }

  if(!userName) {
    return <Login onLogin={setUserName} />;
  }

  return (
    <div>
      <nav>
        <span>{userName}</span>
        <button onClick={() => setPage("calendar")}>캘린더</button>
        <button onClick={() => setPage("actors")}>관심 배우</button>
        <button onClick={() => api.logout().then(() => setUserName(null))}>로그아웃</button>
      </nav>
      {page === "calendar" ? <Calendar /> : <Actors />}
    </div>
  );
}

export default App;
