"""
app.py - AI 门店军师 V2.0 PC端工作台 (Streamlit)
运行命令: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import json
import os
import database
import main as core_logic

# --- 页面配置 ---
st.set_page_config(page_title="AI 门店军师工作台", page_icon="🏪", layout="wide")

# --- 加载/保存本地门店配置 ---
STORE_INFO_FILE = "store_info.json"

def load_store_info():
    if os.path.exists(STORE_INFO_FILE):
        with open(STORE_INFO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"store_name": "", "store_address": "", "contact_phone": "", "current_promotion": ""}

def save_store_info(info_dict):
    with open(STORE_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(info_dict, f, ensure_ascii=False, indent=4)
        
# --- 登录鉴权网关 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- 缩小登录框布局 ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_main, _ = st.columns([1, 2, 1])
    
    with col_main:
        st.title("🏪 AI 门店军师工作台 - 请登录")
        st.markdown("---")
        
        st.subheader("账号密码登录")
        with st.form("login_form"):
            username = st.text_input("用户名", value="admin", placeholder="admin")
            password = st.text_input("密码", type="password", value="888888", placeholder="888888")
            submit = st.form_submit_button("登 录 进 入 系 统", type="primary", use_container_width=True)
            
            if submit:
                # 简易硬编码提权，后期可查数据库
                if username == "admin" and password == "888888":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
                    
        with st.expander("第三方扫码登录 (筹备中)"):
            st.button("🟢 企业微信 一键登录", disabled=True, use_container_width=True)
            st.button("🔵 钉钉 一键登录", disabled=True, use_container_width=True)
            st.button("🟢 飞书 一键登录", disabled=True, use_container_width=True)
            st.info("企业微信/钉钉/飞书 接口调试中，下个版本即将开放 OAuth2.0 授权。")

else:
    # ====== 已登录后的主体程序 ======
    # --- 初始化数据库 ---
    database.init_db()
    
    # --- 侧边栏导航 ---
    st.sidebar.title("🏪 AI 门店军师")
    st.sidebar.markdown(f"**🟢 已登录: 超级管理员**")
    if st.sidebar.button("退出登录"):
        st.session_state.logged_in = False
        st.rerun()
        
    menu = st.sidebar.radio("导航菜单", ["门店配置管理", "客户数据总览", "生成促活话术"])


    # ==========================================
    # 页面 1：门店配置管理
    # ==========================================
    if menu == "门店配置管理":
        st.header("⚙️ 门店配置管理 & AI 营销策划")
        st.markdown("设置本店基础信息，并极速由 AI 生成吸引眼球的客情活动。")
        
        info = load_store_info()
        
        col_form, col_ai = st.columns([1, 1.2], gap="large")
        
        with col_form:
            st.subheader("📝 基础信息配置")
            with st.form("store_info_form"):
                store_name = st.text_input("服务站名称", value=info.get("store_name", ""))
                store_address = st.text_input("服务站地址", value=info.get("store_address", ""))
                contact_phone = st.text_input("联系电话", value=info.get("contact_phone", ""))
                current_promotion = st.text_area("近期主推活动 / 优惠 (非常关键！)", 
                    value=info.get("current_promotion", ""),
                    height=180,
                    help="填写例如：换机油打 8 折、免费洗车等。AI 会在话术末尾顺带一提。")
                    
                submitted = st.form_submit_button("保存配置", use_container_width=True)
                if submitted:
                    save_store_info({
                        "store_name": store_name,
                        "store_address": store_address,
                        "contact_phone": contact_phone,
                        "current_promotion": current_promotion
                    })
                    st.success("配置已保存！")
                    
        with col_ai:
            # --- AI 帮策划区 ---
            st.subheader("💡 AI 营销总监帮策划")
            st.info("不知道推什么活动？只有一个大概想法？让 AI 帮您出谋划策！\n\n生成满意后，请**右键手动复制**并粘贴到左侧的文本框保存。")
            idea_input = st.text_area("输入您的简单灵感：", 
                placeholder="例如：最近天热，想搞个买机油送空调滤芯，清理积碳打对折，主要引流下新面孔。", 
                height=120)
            
            if st.button("✨ 一键生成 3 套专业营销案", type="secondary", use_container_width=True):
                if not idea_input:
                    st.warning("请先简单写几个字的想法~")
                else:
                    try:
                        from openai import OpenAI
                        core_logic.load_dotenv()
                        client = OpenAI(
                            api_key=os.getenv("AI_API_KEY"),
                            base_url=os.getenv("AI_BASE_URL")
                        )
                    except Exception as e:
                        st.error("无法初始化 AI，请确保根目录 .env 已填好密钥。")
                        st.stop()
                        
                    with st.spinner("AI 营销总监正在为您日夜赶稿..."):
                        # 给AI的信息应是当前最新填好的
                        info_for_ai = {"store_name": info.get("store_name")}
                        generated_plans = core_logic.ai_helper_generate_promotion(idea_input, info_for_ai, client)
                        
                        st.success("生成成功！快挑选一套吧：")
                        with st.container(border=True):
                            st.markdown(f"{generated_plans.replace(chr(10), '<br>')}", unsafe_allow_html=True)

    # ==========================================
    # 页面 2：客户数据总览
    # ==========================================
    elif menu == "客户数据总览":
        st.header("👥 客户数据总览")
        
        st.subheader("1. 数据导入与管理")
        col_up, col_del = st.columns([3, 1])
        
        with col_up:
            uploaded_file = st.file_uploader("支持 Excel 格式增量导入", type=["xlsx"])
            if uploaded_file is not None:
                if st.button("📥 开始导入数据库"):
                    temp_path = "temp_uploaded.xlsx"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                        
                    with st.spinner('正在读取并写入数据库...'):
                        try:
                            # 这里调用了健壮的读取逻辑，跳过空行
                            core_logic.read_customer_excel(temp_path)
                            st.success("导入成功！如果发现表格不全，请检查原 Excel 表的表头与空白行。")
                            st.rerun()
                        except Exception as e:
                            st.error(f"导入失败: {e}")
                            
        with col_del:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("🗑️ 清空所有客户记录", type="secondary", use_container_width=True):
                database.delete_all_customers()
                st.success("数据已全部清空！请重新导入新的表格。")
                st.rerun()
                
        st.subheader("2. 数据库全量客户库")
        customers = database.get_all_customers()
        if customers:
            df = pd.DataFrame(customers)
            df = df[['id', 'name', 'car_model', 'last_visit_date', 'last_service']]
            df.columns = ['库ID', '姓名', '车型', '上次到店日期', '上次维修项目']
            
            # 1) 多重过滤器：提取品牌前缀
            df['品牌分类'] = df['车型'].apply(lambda x: str(x)[:2] if x else "未知")
            all_brands = sorted(df['品牌分类'].unique().tolist())
            
            col_f1, col_f2 = st.columns([2, 1])
            with col_f1:
                selected_brands = st.multiselect("🏷️ 筛选汽车品牌:", options=all_brands, default=all_brands)
            with col_f2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔌 同步选定客户至外部 CRM (API)"):
                    st.toast("接口尚未分配，V3 框架预留 API 回调端点。", icon="🚧")
                    
            # 执行过滤
            filtered_df = df[df['品牌分类'].isin(selected_brands)].copy()
            filtered_df = filtered_df.drop(columns=['品牌分类'])
            
            # 2) 行内编辑表盘 - 支持硬分页 (保护内存并确保展示)
            st.markdown("💡 *提示：双击单元格修改「姓名」或「维修项目」（按回车生效）。下方提供 **保存** 和 **撤销** 功能。*")
            
            page_size = 50
            total_pages = max(1, (len(filtered_df) - 1) // page_size + 1)
            
            col_p1, col_p2 = st.columns([1, 4])
            with col_p1:
                current_page = st.number_input(f"📄 翻页 (共 {total_pages} 页)", min_value=1, max_value=total_pages, value=1)
                
            start_idx = (current_page - 1) * page_size
            end_idx = start_idx + page_size
            paged_df = filtered_df.iloc[start_idx:end_idx]
            
            edited_df = st.data_editor(
                paged_df,
                column_config={
                    "库ID": st.column_config.NumberColumn("库ID", disabled=True),
                    "车型": st.column_config.TextColumn("车型", disabled=True),
                    "上次到店日期": st.column_config.TextColumn("上次到店日期", disabled=True)
                },
                use_container_width=True,
                num_rows="fixed",
                key="customer_editor"
            )
            
            # 3) 检测、撤销和保存修改
            try:
                diff = st.session_state["customer_editor"]["edited_rows"]
                if diff:
                    c1, c2, c3 = st.columns([1.5, 1, 3])
                    with c1:
                        if st.button("💾 保存修改至数据库", type="primary", use_container_width=True):
                            for idx_str, changes in diff.items():
                                row_idx = int(idx_str)
                                # 获取这段分页原来的 ID (因为切片导致 iloc 映射的是 paged_df)
                                db_id = paged_df.iloc[row_idx]['库ID']
                                for field_name, new_val in changes.items():
                                    success = database.update_customer_field(db_id, field_name, new_val)
                                    if success:
                                        st.toast(f"记录 ID {db_id} 的 '{field_name}' 已成功更新！")
                            st.success("所有修改已被同步！即将刷新...")
                            # 删除 session 防止弹窗重复
                            del st.session_state["customer_editor"]
                            st.rerun()
                            
                    with c2:
                        if st.button("↩️ 撤销草稿", use_container_width=True):
                            del st.session_state["customer_editor"]
                            st.rerun()
            except Exception as e:
                pass

        else:
            st.info("当前数据库暂无客户记录，请先上传表格。")

    # ==========================================
    # 页面 3：生成促活话术
    # ==========================================
    elif menu == "生成促活话术":
        st.header("🤖 生成促活话术")
        
        customers = database.get_all_customers()
        if not customers:
            st.warning("请先在「客户数据总览」中上传您的客户数据。")
            st.stop()
            
        days_threshold = st.slider("筛选未到店天数阈值：", min_value=30, max_value=365, value=180, step=30)
        
        # 将字典中的字符串日期转回 datetime，复用原 filter 函数
        from datetime import datetime
        for c in customers:
            if isinstance(c['last_visit_date'], str):
                c['上次到店时间'] = datetime.strptime(c['last_visit_date'], "%Y-%m-%d")
            c['姓名'] = c['name']
            c['车型'] = c['car_model']
            c['上次维修项目'] = c['last_service']
                
        inactive = core_logic.filter_inactive_customers(customers, days_threshold=days_threshold)
        
        if inactive:
            st.success(f"找到了 **{len(inactive)}** 位超过 {days_threshold} 天没来的老客户！")
            df_inactive = pd.DataFrame(inactive)[['姓名', '车型', '未到店天数', '上次到店时间', '上次维修项目']]
            st.dataframe(df_inactive, use_container_width=True)
            
            st.markdown("---")
            
            import threading
            
            # 状态机面板
            status = core_logic.bg_generation_status
            
            if not status["is_running"] and len(status["results"]) == 0:
                if st.button("🚀 开始后台批量生成 (不怕切网页)", type="primary"):
                    store_info = load_store_info()
                    try:
                        from openai import OpenAI
                        core_logic.load_dotenv()
                        client = OpenAI(
                            api_key=os.getenv("AI_API_KEY"),
                            base_url=os.getenv("AI_BASE_URL")
                        )
                    except Exception as e:
                        st.error("无法初始化 AI 客户端，请检查 .env。")
                        st.stop()
                        
                    threading.Thread(target=core_logic.bg_generate_worker, args=(inactive, client, store_info)).start()
                    st.rerun()
                    
            elif status["is_running"]:
                st.info(f"🔄 后台引擎正在火力全开... ({status['current']} / {status['total']})")
                
                progress_val = status["current"] / max(1, status["total"])
                st.progress(progress_val)
                
                # 滚动展示最新日志
                log_box = st.empty()
                log_str = "\n".join(status["logs"][-5:])
                log_box.code(log_str)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔄 刷新当前进度"):
                        st.rerun()
                with col_btn2:
                    if st.button("🛑 紧急停止发送请求"):
                        core_logic.bg_generation_status["stop_requested"] = True
                        st.rerun()
            else:
                # 运行已结束（正常完成或中止）
                st.success(f"✅ 执行结束（不论中途是否停止）。共生成 {len(status['results'])} 条可用草稿！")
                
                with st.expander("预览已生成结果", expanded=True):
                    for r in status["results"]:
                        st.markdown(f"**{r['姓名']}**: {r['促活话术']}")
                
                col_clear, col_dl = st.columns(2)
                with col_clear:
                    if st.button("🗑️ 清空结果，重新配置生成"):
                        core_logic.bg_generation_status["results"] = []
                        core_logic.bg_generation_status["logs"] = []
                        st.rerun()
                        
                with col_dl:
                    if len(status["results"]) > 0:
                        core_logic.save_results_to_excel(status["results"], "促活话术_PC导出.xlsx")
                        with open("促活话术_PC导出.xlsx", "rb") as f:
                            st.download_button(
                                label="💾 下载这些话术表格",
                                data=f,
                                file_name="促活话术结果.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
        else:
            st.success(f"太棒了！所有客户都在 {days_threshold} 天内来过店，暂时无需促活。")
            
        # ----------------------------------------
        # V3 Sprint 3: 历史记录面板
        # ----------------------------------------
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.subheader("📜 历史生成库 (Message History)")
        history_records = database.get_message_history()
        
        if history_records:
            st.markdown(f"数据库中共存有 **{len(history_records)}** 条为您保留的历史推文记录。")
            history_df = pd.DataFrame(history_records)
            # 格式化展示
            history_df = history_df[['id', 'customer_name', 'generated_at', 'status', 'message_content']]
            history_df.columns = ['归档ID', '接受者姓名', '生成时间', '状态', '话术原文']
            
            st.data_editor(
                history_df,
                use_container_width=True,
                height=400,
                disabled=["归档ID", "生成时间"],
                key="history_editor"
            )
        else:
            st.info("历史文案记录库为空。生成的文案将会自动存入此列表。")
