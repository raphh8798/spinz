import "../App.css";
import {useState} from "react";
import * as api from "../api";

export default function Login({onLogin}) {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  async function handleSubmit(e){
    e.preventDefault();
    var res = await api.login(name, password);
    if(res.error){
      setError(res.error);
    }else{
      if(res.is_new) alert(res.user_name + "님, 회원가입을 환영합니다!");
      onLogin(res.user_name);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="이름"></input>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="비밀번호"></input>
      <button type="submit">로그인</button>
      {error && <div style={{color: "red"}}>{error}</div>}
    </form>
  );
}
