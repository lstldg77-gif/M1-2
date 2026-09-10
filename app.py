import json
from datetime import date, datetime
from pathlib import Path

import streamlit as st


DATA_FILE = Path(__file__).with_name("local_store.json")


def load_store():
	if not DATA_FILE.exists():
		return {"data": [], "conversations": []}
	try:
		return json.loads(DATA_FILE.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		return {"data": [], "conversations": []}


def save_store(store):
	DATA_FILE.write_text(
		json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
	)


def summarize(items):
	values = [float(item["value"]) for item in items]
	total = sum(values)
	return {
		"count": len(items),
		"total": round(total, 2),
		"average": round(total / len(values), 2) if values else 0,
		"latest": items[-1]["date"] if items else "기록 없음",
	}


def mock_reply(message, summary):
	return (
		f"현재 {summary['count']}개 세션에서 총 {summary['total']}곡(또는 작업 단위)을 "
		f"기록했고, 평균은 {summary['average']}입니다. 최근 기록일은 "
		f"{summary['latest']}입니다. 질문하신 '{message}'에 대해서는 최근 데이터와 "
		"작업 메모를 함께 확인해 다음 제작 일정을 조정해 보세요."
	)


st.set_page_config(page_title="음악 제작 AI 비서", page_icon="♪", layout="wide")
st.title("음악 제작 AI 비서")
st.caption("제작 데이터를 관리하고, 기록을 바탕으로 작업 인사이트를 받아보세요.")

store = load_store()
items = sorted(store["data"], key=lambda item: item["date"])
summary = summarize(items)

metric_columns = st.columns(4)
metric_columns[0].metric("기록 세션", summary["count"])
metric_columns[1].metric("총 작업량", summary["total"])
metric_columns[2].metric("평균 작업량", summary["average"])
metric_columns[3].metric("최근 기록", summary["latest"])

data_tab, chat_tab, history_tab = st.tabs(["데이터 관리", "AI 채팅", "대화 기록"])

with data_tab:
	st.subheader("제작 데이터")
	with st.form("add_data", clear_on_submit=True):
		input_date = st.date_input("날짜", value=date.today())
		input_value = st.number_input("작업량", min_value=0.0, step=1.0)
		input_memo = st.text_input("메모")
		if st.form_submit_button("데이터 추가", type="primary"):
			store["data"].append(
				{
					"id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
					"date": input_date.isoformat(),
					"value": input_value,
					"memo": input_memo,
				}
			)
			save_store(store)
			st.success("데이터가 저장되었습니다.")
			st.rerun()

	for item in items:
		with st.container(border=True):
			columns = st.columns([1.2, 1, 3, 0.8])
			columns[0].write(item["date"])
			columns[1].write(item["value"])
			columns[2].write(item.get("memo", ""))
			if columns[3].button("삭제", key=f"delete-{item['id']}"):
				store["data"] = [
					saved for saved in store["data"] if saved["id"] != item["id"]
				]
				save_store(store)
				st.rerun()

with chat_tab:
	st.subheader("데이터 기반 AI 채팅")
	for message in st.session_state.get("chat_messages", []):
		with st.chat_message(message["role"]):
			st.write(message["content"])
	prompt = st.chat_input("제작 현황이나 다음 작업을 질문해 보세요")
	if prompt:
		st.session_state.setdefault("chat_messages", []).append(
			{"role": "user", "content": prompt}
		)
		with st.chat_message("user"):
			st.write(prompt)
		with st.chat_message("assistant"):
			with st.spinner("데이터를 분석하고 답변을 만드는 중..."):
				reply = mock_reply(prompt, summary)
				st.write(reply)
		st.session_state["chat_messages"].append(
			{"role": "assistant", "content": reply}
		)

with history_tab:
	st.subheader("대화 기록")
	conversations = store["conversations"]
	if not conversations:
		st.info("저장된 대화가 없습니다. AI 채팅을 시작해 보세요.")
	for conversation in conversations:
		with st.expander(conversation["title"]):
			for message in conversation["messages"]:
				st.markdown(f"**{message['role']}**: {message['content']}")