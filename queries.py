"""
SQL 쿼리 함수 - app.py 라우트에서 사용. 커밋은 app.py에서 관리 (cur만 받음).
"""

from werkzeug.security import generate_password_hash, check_password_hash



def get_or_create_user(cur, name, password):
    cur.execute("SELECT ID, PASSWORD_HASH FROM USERS WHERE NAME = %s", (name,))
    result = cur.fetchone()
    if result:
        if check_password_hash(result["password_hash"], password):
            return result["id"], False   # 기존 사용자
        return None, False   # 비밀번호 틀림

    cur.execute(
        "INSERT INTO USERS(NAME, PASSWORD_HASH) VALUES (%s, %s) RETURNING ID",
        (name, generate_password_hash(password)),
    )
    return cur.fetchone()["id"], True


# 해당 월 개막작 목록 + 현재 사용자의 찜 여부
def get_calendar_performances(cur, user_id: int, year: int, month: int):
    cur.execute(
        """
            SELECT P.MT20ID, P.PRFNM, P.PRFPDFROM, P.PRFPDTO
                 , CASE WHEN F.USER_ID IS NOT NULL THEN TRUE ELSE FALSE END AS IS_FAV
                 , W.ID AS ACTOR_ID, W.ACTOR_NAME
              FROM PERFORM_MASTER P
                   LEFT JOIN PERFORM_FAV F
                     ON P.MT20ID  = F.MT20ID
                    AND F.USER_ID = %s
                   LEFT JOIN PERFORM_DETAIL D
                     ON P.MT20ID  = D.MT20ID
                   LEFT JOIN WATCHED_ACTOR W
                     ON W.USER_ID = %s
                    AND W.ACTOR_NAME = ANY(SELECT TRIM(X) FROM UNNEST(STRING_TO_ARRAY(D.PRFCAST, ',')) AS X)
             WHERE EXTRACT(YEAR FROM P.PRFPDFROM)  = %s
               AND EXTRACT(MONTH FROM P.PRFPDFROM) = %s
             ORDER BY P.PRFPDFROM
        """,
        (user_id, user_id, year, month),
    )
    return cur.fetchall()


# DELETE 먼저 시도 / 있으면 지우고 없으면 추가
def toggle_favorite(cur, user_id: int, mt20id: str):
    cur.execute(
        "DELETE FROM PERFORM_FAV WHERE USER_ID = %s AND MT20ID = %s",
        (user_id, mt20id),
    )

    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO PERFORM_FAV(USER_ID, MT20ID) VALUES (%s, %s)",
            (user_id, mt20id),
        )


def list_watched_actors(cur, user_id: int):
    cur.execute(
        "SELECT ID, ACTOR_NAME FROM WATCHED_ACTOR WHERE USER_ID = %s ORDER BY ACTOR_NAME",
        (user_id,),
    )
    return cur.fetchall()


def add_watched_actor(cur, user_id: int, actor_name: str):
    cur.execute(
        """
            INSERT INTO WATCHED_ACTOR (USER_ID, ACTOR_NAME)
            VALUES (%s, %s)
            ON CONFLICT (USER_ID, ACTOR_NAME) DO NOTHING
        """,
        (user_id, actor_name),
    )


def delete_watched_actor(cur, user_id: int, actor_id: int):
    cur.execute(
        "DELETE FROM WATCHED_ACTOR WHERE ID = %s AND USER_ID = %s",
        (actor_id, user_id),
    )


def _build_actor_filter_query(actor_names: list[str]) -> tuple[str, list[str]]:
    base_sql = """
                SELECT EXTRACT(YEAR FROM P.PRFPDFROM) AS STYEAR
                     , P.MT20ID, P.PRFNM, P.PRFPDFROM, P.PRFPDTO, P.FCLTYNM, D.PRFCAST
                  FROM PERFORM_MASTER P
                       INNER JOIN PERFORM_DETAIL D
                          ON D.MT20ID = P.MT20ID
                 WHERE {where}
                 ORDER BY P.PRFPDFROM
              """
    
    if not actor_names:
        return base_sql.format(where="FALSE"), []

    where = " OR ".join(["%s = ANY(SELECT TRIM(X) FROM UNNEST(STRING_TO_ARRAY(D.PRFCAST, ',')) AS X)"] * len(actor_names))
    return base_sql.format(where=where), actor_names


def get_performances_by_actors(cur, actor_names: list[str]):
    query, params = _build_actor_filter_query(actor_names)
    cur.execute(query, params)
    return cur.fetchall()
