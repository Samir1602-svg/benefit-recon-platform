import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import io
from datetime import datetime

# ==========================================
# 1. DATABASE & SECURITY LAYER (SQLite + Auth)
# ==========================================
DB_FILE = "benefit_audit_enterprise.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_database():
    conn = get_db()
    c = conn.cursor()
    
    # 1. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # 2. Dynamic Job Aids / Business Rules Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_aid_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            rule_title TEXT NOT NULL,
            rule_description TEXT NOT NULL,
            error_type TEXT NOT NULL,
            clarification_action TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Audit Logs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audited_by TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan_count INTEGER,
            total_rows INTEGER,
            type1_errors INTEGER,
            type2_errors INTEGER,
            accuracy_score REAL
        )
    ''')
    
    # Seed default Admin & Analyst users if first time
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                  ("admin", hash_password("admin@123"), "Lead Software Developer / Admin", "ADMIN"))
        c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                  ("analyst", hash_password("analyst@123"), "Benefit Operations Analyst", "ANALYST"))
                  
    # Seed default Job Aids
    c.execute("SELECT COUNT(*) FROM job_aid_rules")
    if c.fetchone()[0] == 0:
        seed_rules = [
            ("JA-COPAY-01", "Cost Share", "Copay Direct Match", "Copay amount must strictly match the Source Benefit Summary grid.", "Type 1: Financial Mismatch (Copay)", "Direct financial discrepancy. Coder must update copay table in system."),
            ("JA-COINS-01", "Cost Share", "Coinsurance Split Match", "Coinsurance percentage must align with benefit booklet schedule.", "Type 1: Financial Mismatch (Coinsurance)", "Direct financial discrepancy. Coder must reconfigure coinsurance percentage split."),
            ("JA-DED-01", "Accumulators / ACA", "Preventive Deductible Mandate", "ACA Preventive services must be 100% covered ($0 copay) with Deductible = No.", "Type 2: Policy / ACA Mandate Clarification", "Clarification: Preventive services cannot have deductible accumulator per ACA Section 2713."),
            ("JA-AUTH-01", "Utilization Mgmt", "Prior Authorization Flag Check", "Inpatient and High-Cost radiology require Prior-Auth match.", "Type 2: Workflow / Auth Rule Clarification", "Clarification: Prior authorization indicator differs from standard job aid matrix.")
        ]
        c.executemany("INSERT INTO job_aid_rules (rule_code, category, rule_title, rule_description, error_type, clarification_action) VALUES (?, ?, ?, ?, ?, ?)", seed_rules)

    conn.commit()
    conn.close()

init_database()

def authenticate(username, password):
    conn = get_db()
    c = conn.cursor()
    pw_hash = hash_password(password)
    c.execute("SELECT username, full_name, role FROM users WHERE username = ? AND password_hash = ?", (username, pw_hash))
    user = c.fetchone()
    conn.close()
    return user

# ==========================================
# 2. STREAMLIT APP CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="BenefitRecon Pro | Enterprise Audit Platform",
    page_icon="🛡️",
    layout="wide"
)

st.markdown('''
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 8px;
    }
    .admin-badge {
        background-color: #4338CA;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .analyst-badge {
        background-color: #0284C7;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
''', unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["full_name"] = None
    st.session_state["role"] = None

# ==========================================
# 3. LOGIN SCREEN
# ==========================================
if not st.session_state["authenticated"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ BenefitRecon Enterprise</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Payer Benefit Configuration Audit & Dynamic Rules Engine</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.subheader("Employee Sign In")
            u_name = st.text_input("Username / Employee ID")
            u_pass = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Sign In", use_container_width=True)
            
            if btn_login:
                user_record = authenticate(u_name.strip(), u_pass.strip())
                if user_record:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_record[0]
                    st.session_state["full_name"] = user_record[1]
                    st.session_state["role"] = user_record[2]
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Please check your credentials.")
        
        st.markdown("---")
        st.caption("💡 **Default Credentials for Testing:**")
        st.caption("- **Admin/Developer:** `admin` | Password: `admin@123`")
        st.caption("- **Benefit Analyst:** `analyst` | Password: `analyst@123`")
    st.stop()

# ==========================================
# 4. AUTHENTICATED NAVIGATION & SIDEBAR
# ==========================================
user_role = st.session_state["role"]
full_name = st.session_state["full_name"]

with st.sidebar:
    st.markdown(f"### 👤 Logged in as:")
    st.write(f"**{full_name}**")
    if user_role == "ADMIN":
        st.markdown('<span class="admin-badge">Software Developer / Admin</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="analyst-badge">Benefit Analyst</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    nav_options = ["🔍 Run Benefit Audit", "📊 Audit History & Analytics"]
    if user_role == "ADMIN":
        nav_options.extend(["⚙️ Job Aid & Rules Engine Manager", "👥 Employee Access Control"])
        
    selected_page = st.radio("Navigation Menu", nav_options)
    
    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["full_name"] = None
        st.session_state["role"] = None
        st.rerun()

# ==========================================
# PAGE 1: RUN BENEFIT AUDIT
# ==========================================
def clean_val(val):
    if pd.isna(val):
        return ""
    return str(val).replace("$", "").replace("%", "").strip().upper()

if selected_page == "🔍 Run Benefit Audit":
    st.title("🩺 Benefit Configuration & Cost-Share Audit")
    st.caption("Upload the Benchmark Source Grid and Coder System Export to auto-reconcile discrepancies against active Job Aids.")

    colA, colB = st.columns(2)
    with colA:
        src_file = st.file_uploader("1. Source Plan / Benchmark Grid (.xlsx)", type=["xlsx", "xls"], key="src")
    with colB:
        cod_file = st.file_uploader("2. System Coded / Coder Export (.xlsx)", type=["xlsx", "xls"], key="cod")

    if src_file and cod_file:
        try:
            df_src = pd.read_excel(src_file, engine='openpyxl')
            df_cod = pd.read_excel(cod_file, engine='openpyxl')
            
            conn = get_db()
            rules_df = pd.read_sql_query("SELECT * FROM job_aid_rules WHERE is_active = 1", conn)
            conn.close()
            
            if "Plan_ID" not in df_src.columns or "Benefit_Service" not in df_src.columns:
                st.error("Uploaded files must have 'Plan_ID' and 'Benefit_Service' columns.")
                st.stop()

            merged = pd.merge(df_src, df_cod, on=["Plan_ID", "Benefit_Service"], suffixes=('_Source', '_Coded'), how='outer')
            discrepancies = []

            for _, row in merged.iterrows():
                plan = row.get("Plan_ID", "N/A")
                service = row.get("Benefit_Service", "N/A")

                # Copay Check
                if "Copay_Source" in row and "Copay_Coded" in row:
                    if clean_val(row["Copay_Source"]) != clean_val(row["Copay_Coded"]):
                        rule = rules_df[rules_df["rule_code"] == "JA-COPAY-01"]
                        rule_desc = rule["clarification_action"].values[0] if not rule.empty else "Copay value mismatch."
                        discrepancies.append({
                            "Plan_ID": plan,
                            "Benefit_Service": service,
                            "Field_Audited": "Copay",
                            "Source_Benchmark": row["Copay_Source"],
                            "System_Coded": row["Copay_Coded"],
                            "Error_Type": "Type 1: Financial Mismatch",
                            "Job_Aid_Code": "JA-COPAY-01",
                            "Action_Clarification": rule_desc
                        })

                # Coinsurance Check
                if "Coinsurance_Source" in row and "Coinsurance_Coded" in row:
                    if clean_val(row["Coinsurance_Source"]) != clean_val(row["Coinsurance_Coded"]):
                        rule = rules_df[rules_df["rule_code"] == "JA-COINS-01"]
                        rule_desc = rule["clarification_action"].values[0] if not rule.empty else "Coinsurance percentage mismatch."
                        discrepancies.append({
                            "Plan_ID": plan,
                            "Benefit_Service": service,
                            "Field_Audited": "Coinsurance (%)",
                            "Source_Benchmark": row["Coinsurance_Source"],
                            "System_Coded": row["Coinsurance_Coded"],
                            "Error_Type": "Type 1: Financial Mismatch",
                            "Job_Aid_Code": "JA-COINS-01",
                            "Action_Clarification": rule_desc
                        })

                # Deductible Check
                if "Deductible_Applies_Source" in row and "Deductible_Applies_Coded" in row:
                    if clean_val(row["Deductible_Applies_Source"]) != clean_val(row["Deductible_Applies_Coded"]):
                        rule = rules_df[rules_df["rule_code"] == "JA-DED-01"]
                        rule_desc = rule["clarification_action"].values[0] if not rule.empty else "Deductible accumulator mismatch."
                        discrepancies.append({
                            "Plan_ID": plan,
                            "Benefit_Service": service,
                            "Field_Audited": "Deductible Applies Flag",
                            "Source_Benchmark": row["Deductible_Applies_Source"],
                            "System_Coded": row["Deductible_Applies_Coded"],
                            "Error_Type": "Type 2: Policy / Job Aid Clarification",
                            "Job_Aid_Code": "JA-DED-01",
                            "Action_Clarification": rule_desc
                        })

            err_df = pd.DataFrame(discrepancies)
            total_checked = len(merged)
            total_err = len(err_df)
            t1 = len(err_df[err_df["Error_Type"].str.contains("Type 1", na=False)]) if total_err > 0 else 0
            t2 = len(err_df[err_df["Error_Type"].str.contains("Type 2", na=False)]) if total_err > 0 else 0
            acc = round(((total_checked - total_err) / total_checked) * 100, 1) if total_checked > 0 else 100

            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Rows Processed", total_checked)
            m2.metric("Type 1 Errors (Financial)", t1, delta=f"-{t1}" if t1 > 0 else "0", delta_color="inverse")
            m3.metric("Type 2 Errors (Clarification)", t2, delta=f"-{t2}" if t2 > 0 else "0", delta_color="inverse")
            m4.metric("Coder Configuration Accuracy", f"{acc}%")

            if st.button("💾 Save Audit Results to History Log"):
                conn = get_db()
                c = conn.cursor()
                plans_count = merged["Plan_ID"].nunique()
                c.execute("INSERT INTO audit_logs (audited_by, plan_count, total_rows, type1_errors, type2_errors, accuracy_score) VALUES (?, ?, ?, ?, ?, ?)",
                          (st.session_state["username"], plans_count, total_checked, t1, t2, acc))
                conn.commit()
                conn.close()
                st.success("✅ Audit log successfully saved to enterprise database.")

            st.subheader(f"⚠️ Discrepancy Log ({total_err} Issues Detected)")
            if total_err > 0:
                st.dataframe(err_df, use_container_width=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    err_df.to_excel(writer, sheet_name="Errors_and_Clarifications", index=False)
                    merged.to_excel(writer, sheet_name="Raw_Comparison", index=False)
                buffer.seek(0)
                
                st.download_button(
                    label="📥 Export Audit & Clarification Report (Excel)",
                    data=buffer,
                    file_name=f"Benefit_Audit_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.balloons()
                st.success("✅ 100% Match! No discrepancies found.")

        except Exception as e:
            st.error(f"Error during audit run: {str(e)}")

# ==========================================
# PAGE 2: AUDIT HISTORY & ANALYTICS
# ==========================================
elif selected_page == "📊 Audit History & Analytics":
    st.title("📊 Enterprise Audit History & Quality Analytics")
    st.caption("Track past audit runs, accuracy rates, and operational quality metrics.")
    
    conn = get_db()
    logs_df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", conn)
    conn.close()
    
    if logs_df.empty:
        st.info("No audit logs recorded yet. Run an audit and click 'Save Audit Results' to populate data.")
    else:
        st.dataframe(logs_df, use_container_width=True)

# ==========================================
# PAGE 3: JOB AID & RULES ENGINE MANAGER (ADMIN ONLY)
# ==========================================
elif selected_page == "⚙️ Job Aid & Rules Engine Manager":
    st.title("⚙️ Developer Control: Job Aid & Rules Manager")
    st.info("As the System Developer/Admin, you can dynamically create, edit, or toggle rules and clarifications without restarting the application.")
    
    conn = get_db()
    rules_df = pd.read_sql_query("SELECT * FROM job_aid_rules", conn)
    conn.close()
    
    st.subheader("📋 Active Business Rules & Job Aids")
    st.dataframe(rules_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("➕ Add New Job Aid / Clarification Rule")
    
    with st.form("new_rule_form"):
        r_code = st.text_input("Rule Code (e.g., JA-TIER-02, JA-STATE-01)")
        r_cat = st.selectbox("Category", ["Cost Share", "Accumulators / ACA", "Utilization Mgmt", "State Mandate", "Network Tier"])
        r_title = st.text_input("Rule Title")
        r_desc = st.text_area("Rule Description (Condition to check)")
        r_type = st.selectbox("Error Classification", ["Type 1: Financial Mismatch", "Type 2: Policy / Job Aid Clarification"])
        r_action = st.text_area("Clarification & Action Required (Guidance message for coder)")
        
        btn_add = st.form_submit_button("Publish Rule to Production")
        if btn_add:
            if r_code and r_title and r_action:
                try:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO job_aid_rules (rule_code, category, rule_title, rule_description, error_type, clarification_action) VALUES (?, ?, ?, ?, ?, ?)",
                              (r_code.strip().upper(), r_cat, r_title, r_desc, r_type, r_action))
                    conn.commit()
                    conn.close()
                    st.success(f"Rule `{r_code}` successfully added to the live rule engine!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding rule: {str(e)}")
            else:
                st.warning("Please fill all mandatory fields.")

# ==========================================
# PAGE 4: EMPLOYEE ACCESS CONTROL (ADMIN ONLY)
# ==========================================
elif selected_page == "👥 Employee Access Control":
    st.title("👥 Employee Access & Identity Management")
    st.caption("Create unique logins, passwords, and assign roles (Benefit Analyst vs Developer/Admin).")
    
    conn = get_db()
    users_df = pd.read_sql_query("SELECT id, username, full_name, role FROM users", conn)
    conn.close()
    
    st.subheader("Registered Employees")
    st.dataframe(users_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("➕ Register New Employee")
    
    with st.form("new_user_form"):
        new_u = st.text_input("Username / Employee ID")
        new_name = st.text_input("Full Name")
        new_pw = st.text_input("Temporary Password", type="password")
        new_role = st.selectbox("Assign Role", ["ANALYST", "ADMIN"])
        
        btn_user = st.form_submit_button("Create Employee Account")
        if btn_user:
            if new_u and new_pw and new_name:
                try:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                              (new_u.strip(), hash_password(new_pw.strip()), new_name.strip(), new_role))
                    conn.commit()
                    conn.close()
                    st.success(f"Account for {new_name} ({new_role}) created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating user: {str(e)}")
            else:
                st.warning("Please fill all user details.")