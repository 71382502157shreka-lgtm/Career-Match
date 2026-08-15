import os
import sys
import tempfile
import streamlit as st
from datetime import datetime

# Ensure app package is importable across different root/deployment directory structures
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)

for path in [current_dir, parent_dir, root_dir]:
    if os.path.exists(os.path.join(path, "app")) and path not in sys.path:
        sys.path.insert(0, path)

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.job import JobPosting
from app.models.application import Application
from app.services.ai_matcher import ai_matcher
from app.services.resume_parser import extract_text_from_pdf, extract_skills, skills_to_csv
from app.core.security import get_password_hash, verify_password

# Initialize Database Schema
Base.metadata.create_all(bind=engine)

# Set Page Config
st.set_page_config(
    page_title="AI Job Finder & Matcher",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Dark/Gradient Theme
st.markdown("""
<style>
    /* Main Background & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }

    /* Cards and Containers */
    .css-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .css-card:hover {
        border-color: rgba(99, 102, 241, 0.5);
    }

    /* Match Score Badges */
    .match-badge-high {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 700;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        font-size: 0.95rem;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    .match-badge-mid {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-weight: 700;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        font-size: 0.95rem;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    .match-badge-low {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        font-weight: 700;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        font-size: 0.95rem;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }

    /* Skill Tags */
    .skill-tag {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.82rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        display: inline-block;
    }
    .skill-tag-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.82rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        display: inline-block;
    }
    .skill-tag-match {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.82rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        display: inline-block;
    }

    /* Status Badges */
    .status-applied { background-color: #3b82f6; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .status-shortlisted { background-color: #10b981; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .status-hired { background-color: #8b5cf6; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .status-rejected { background-color: #ef4444; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }

    /* Custom Header Banner */
    .header-title {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# Helper Database Dependency Context Manager
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Session State Initialization
if "user" not in st.session_state:
    st.session_state["user"] = None

# Helper to render match badge HTML
def render_match_badge(score: float):
    if score >= 80:
        return f'<span class="match-badge-high">🔥 {score:.1f}% Match</span>'
    elif score >= 50:
        return f'<span class="match-badge-mid">⚡ {score:.1f}% Match</span>'
    else:
        return f'<span class="match-badge-low">💡 {score:.1f}% Match</span>'

# Sidebar Setup
with st.sidebar:
    st.markdown('<h2 class="header-title">🤖 AI Job Finder</h2>', unsafe_allow_html=True)
    st.caption("AI-Powered Resume Matching & Job Portal")
    st.markdown("---")

    user = st.session_state["user"]
    if user:
        st.write(f"👤 **{user['full_name']}**")
        st.caption(f"Role: `{user['role'].capitalize()}` | {user['email']}")
        st.markdown("---")

        if user["role"] == "candidate":
            nav_option = st.radio(
                "Navigation",
                ["🎯 AI Job Recommendations", "📄 My Profile & Resume", "📋 My Applications", "⚡ AI Sandbox Playground"],
                index=0
            )
        else: # recruiter
            nav_option = st.radio(
                "Navigation",
                ["➕ Post New Job", "💼 Manage Job Listings", "👥 Applicant Ranking", "⚡ AI Sandbox Playground"],
                index=0
            )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()
    else:
        nav_option = st.radio(
            "Navigation",
            ["🔐 Login / Register", "⚡ AI Sandbox Playground"],
            index=0
        )

# -----------------------------------------------------------------------------
# PAGE: LOGIN & REGISTRATION
# -----------------------------------------------------------------------------
if not st.session_state["user"] and nav_option == "🔐 Login / Register":
    st.markdown('<h1 class="header-title">Welcome to AI Job Finder</h1>', unsafe_allow_html=True)
    st.markdown("Log in or create an account to start matching with jobs or finding top candidates.")
    
    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

    with tab_login:
        st.subheader("Sign In")
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@example.com")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In", use_container_width=True)

            if submit_login:
                if not email or not password:
                    st.error("Please provide both email and password.")
                else:
                    db = get_db()
                    db_user = db.query(User).filter(User.email == email.strip()).first()
                    if db_user and verify_password(password, db_user.hashed_password):
                        st.session_state["user"] = {
                            "id": db_user.id,
                            "email": db_user.email,
                            "full_name": db_user.full_name,
                            "role": db_user.role,
                        }
                        st.success(f"Welcome back, {db_user.full_name}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                    db.close()

    with tab_register:
        st.subheader("Register New Account")
        with st.form("register_form"):
            full_name = st.text_input("Full Name", placeholder="Jane Doe")
            reg_email = st.text_input("Email Address", placeholder="jane@example.com")
            reg_password = st.text_input("Password", type="password")
            role = st.selectbox("I am a:", ["candidate", "recruiter"], format_func=lambda x: "💼 Candidate (Job Seeker)" if x=="candidate" else "🏢 Recruiter / Employer")
            submit_reg = st.form_submit_button("Create Account", use_container_width=True)

            if submit_reg:
                if not full_name or not reg_email or not reg_password:
                    st.error("All fields are required.")
                else:
                    db = get_db()
                    existing = db.query(User).filter(User.email == reg_email.strip()).first()
                    if existing:
                        st.error("Email is already registered. Please sign in.")
                    else:
                        new_user = User(
                            full_name=full_name.strip(),
                            email=reg_email.strip(),
                            hashed_password=get_password_hash(reg_password),
                            role=role
                        )
                        db.add(new_user)
                        db.commit()
                        db.refresh(new_user)
                        st.session_state["user"] = {
                            "id": new_user.id,
                            "email": new_user.email,
                            "full_name": new_user.full_name,
                            "role": new_user.role,
                        }
                        st.success("Account created successfully!")
                        st.rerun()
                    db.close()

# -----------------------------------------------------------------------------
# PAGE: AI PLAYGROUND / SANDBOX
# -----------------------------------------------------------------------------
elif nav_option == "⚡ AI Sandbox Playground":
    st.markdown('<h1 class="header-title">⚡ Interactive AI Job Matcher Sandbox</h1>', unsafe_allow_html=True)
    st.write("Test candidate skills and resume text against any job posting in real time without storing data.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 Candidate Profile")
        sandbox_skills = st.text_area("Candidate Skills (comma separated)", "python, fastapi, sql, docker, scikit-learn", height=100)
        sandbox_resume = st.text_area("Extracted Resume Text", "Experienced software engineer specializing in backend APIs with FastAPI, database optimization with PostgreSQL, and building AI matching algorithms.", height=200)
    
    with col2:
        st.subheader("🏢 Job Posting")
        sandbox_job_title = st.text_input("Job Title", "Senior AI Backend Engineer")
        sandbox_req_skills = st.text_area("Required Job Skills", "python, fastapi, sql, docker, kubernetes, machine learning", height=100)
        sandbox_job_desc = st.text_area("Job Description", "We are seeking a backend engineer to lead our AI recommendation platform. Experience with Python, FastAPI, SQL, Docker, ML algorithms, and cloud deployments.", height=200)

    if st.button("🚀 Calculate AI Compatibility Match", type="primary", use_container_width=True):
        class TempJob:
            def __init__(self, title, description, required_skills):
                self.title = title
                self.description = description
                self.required_skills = required_skills
        
        temp_job = TempJob(sandbox_job_title, sandbox_job_desc, sandbox_req_skills)
        score = ai_matcher.match_candidate_to_job(sandbox_skills, sandbox_resume, temp_job)
        missing_skills = ai_matcher.skill_gap(sandbox_skills, sandbox_req_skills)

        candidate_skill_list = [s.strip().lower() for s in sandbox_skills.split(",") if s.strip()]
        req_skill_list = [s.strip().lower() for s in sandbox_req_skills.split(",") if s.strip()]
        matched_skills = [s for s in req_skill_list if s in candidate_skill_list]

        st.markdown("---")
        st.markdown("### 📊 Matching Results")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("AI Match Percentage", f"{score}%")
        with m2:
            st.metric("Matching Skills Count", f"{len(matched_skills)} / {len(req_skill_list)}")
        with m3:
            st.metric("Missing Skills Count", f"{len(missing_skills)}")

        st.progress(min(score / 100.0, 1.0))

        c_match, c_missing = st.columns(2)
        with c_match:
            st.markdown("#### ✅ Matching Skills Overlap")
            if matched_skills:
                tags_html = "".join([f'<span class="skill-tag-match">✓ {s}</span>' for s in matched_skills])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.write("No direct skill matches found.")

        with c_missing:
            st.markdown("#### ⚠️ Skill Gap (Missing Required Skills)")
            if missing_skills:
                tags_html = "".join([f'<span class="skill-tag-missing">✗ {s}</span>' for s in missing_skills])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.success("Candidate possesses all required skills!")

# -----------------------------------------------------------------------------
# PAGE: CANDIDATE - PROFILE & RESUME
# -----------------------------------------------------------------------------
elif nav_option == "📄 My Profile & Resume" and st.session_state["user"]:
    db = get_db()
    current_user = db.query(User).filter(User.id == st.session_state["user"]["id"]).first()

    st.markdown('<h1 class="header-title">📄 My Resume & Profile</h1>', unsafe_allow_html=True)

    col_resume, col_profile = st.columns([1, 1])

    with col_resume:
        st.subheader("📤 PDF Resume Auto-Parser")
        st.write("Upload your PDF resume to automatically extract text and detect skills.")
        
        uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
        if uploaded_file is not None:
            if st.button("⚡ Parse & Extract Resume Data", type="primary"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                try:
                    extracted_text = extract_text_from_pdf(tmp_path)
                    detected_skills = extract_skills(extracted_text)

                    # Merge existing skills with detected
                    existing_list = [s.strip() for s in current_user.skills.split(",") if s.strip()] if current_user.skills else []
                    all_skills = list(set([s.lower() for s in existing_list] + detected_skills))

                    current_user.resume_text = extracted_text
                    current_user.skills = skills_to_csv(all_skills)
                    db.commit()
                    db.refresh(current_user)

                    st.success(f"Resume parsed! Detected {len(detected_skills)} skills.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing PDF: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

        st.markdown("---")
        st.subheader("Extracted Resume Text Preview")
        if current_user.resume_text:
            st.text_area("Extracted Text", current_user.resume_text, height=300, disabled=True)
        else:
            st.info("No resume uploaded yet. Upload a PDF above to populate this section.")

    with col_profile:
        st.subheader("👤 Edit Profile Details")
        with st.form("profile_form"):
            p_full_name = st.text_input("Full Name", current_user.full_name)
            p_headline = st.text_input("Headline / Current Role", current_user.headline or "")
            p_skills = st.text_area("Skills (comma-separated)", current_user.skills or "", help="Comma separated list of skills e.g. python, sql, react")
            
            c1, c2 = st.columns(2)
            with c1:
                p_exp = st.number_input("Years of Experience", min_value=0, max_value=50, value=current_user.experience_years or 0)
                p_location = st.text_input("Location", current_user.location or "")
            with c2:
                p_degree = st.text_input("Highest Degree", current_user.degree or "")
                p_salary = st.number_input("Expected Annual Salary ($)", min_value=0.0, value=float(current_user.expected_salary or 0.0), step=5000.0)
            
            p_linkedin = st.text_input("LinkedIn Profile URL", current_user.linkedin_url or "")
            p_github = st.text_input("GitHub Profile URL", current_user.github_url or "")

            save_profile = st.form_submit_button("Save Profile Updates", use_container_width=True)
            if save_profile:
                current_user.full_name = p_full_name
                current_user.headline = p_headline
                current_user.skills = p_skills
                current_user.experience_years = p_exp
                current_user.location = p_location
                current_user.degree = p_degree
                current_user.expected_salary = p_salary
                current_user.linkedin_url = p_linkedin
                current_user.github_url = p_github
                db.commit()
                st.success("Profile details updated successfully!")
                st.rerun()

    db.close()

# -----------------------------------------------------------------------------
# PAGE: CANDIDATE - AI JOB RECOMMENDATIONS
# -----------------------------------------------------------------------------
elif nav_option == "🎯 AI Job Recommendations" and st.session_state["user"]:
    db = get_db()
    current_user = db.query(User).filter(User.id == st.session_state["user"]["id"]).first()

    st.markdown('<h1 class="header-title">🎯 AI Recommended Jobs</h1>', unsafe_allow_html=True)
    
    if not current_user.skills and not current_user.resume_text:
        st.warning("⚠️ Your profile skills and resume are currently empty. Please update your profile or upload a resume to get accurate AI job recommendations!")
    
    # Filter options
    col_search, col_score, col_workplace = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Keyword (Title, Company, Skill)", "")
    with col_score:
        min_score = st.slider("Min AI Match Score", 0, 100, 0)
    with col_workplace:
        workplace_filter = st.selectbox("Workplace Type", ["All", "Remote", "Hybrid", "On-site"])

    jobs = db.query(JobPosting).all()
    
    if not jobs:
        st.info("No job postings available yet. Check back soon!")
    else:
        # Rank jobs using AI Matcher
        ranked_jobs = ai_matcher.rank_jobs_for_candidate(
            current_user.skills or "",
            current_user.resume_text or "",
            jobs
        )

        # Existing candidate applications
        existing_apps = {app.job_id: app for app in db.query(Application).filter(Application.candidate_id == current_user.id).all()}

        filtered_count = 0
        for job, score in ranked_jobs:
            if score < min_score:
                continue
            if workplace_filter != "All" and job.workplace_type != workplace_filter:
                continue
            if search_query:
                q = search_query.lower()
                if q not in job.title.lower() and q not in job.company.lower() and q not in job.required_skills.lower():
                    continue

            filtered_count += 1
            missing_skills = ai_matcher.skill_gap(current_user.skills or "", job.required_skills)
            candidate_skill_list = [s.strip().lower() for s in (current_user.skills or "").split(",") if s.strip()]
            req_skill_list = [s.strip().lower() for s in job.required_skills.split(",") if s.strip()]
            matching_skills = [s for s in req_skill_list if s in candidate_skill_list]

            # Render Job Card
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            head_col1, head_col2 = st.columns([3, 1])
            
            with head_col1:
                st.markdown(f"### {job.title}")
                st.markdown(f"**🏢 {job.company}** | 📍 {job.location} | 💼 {job.job_type} | 🏠 {job.workplace_type}")
                salary_str = f"${job.salary_min:,.0f} - ${job.salary_max:,.0f}" if job.salary_min and job.salary_max else "Competitive"
                st.caption(f"💰 Salary: {salary_str} | ⏳ Experience: {job.experience_years}+ years")
            
            with head_col2:
                st.markdown(render_match_badge(score), unsafe_allow_html=True)

            st.markdown("---")
            
            # Skills Breakdown
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.markdown("**Required Skills:**")
                req_html = "".join([f'<span class="skill-tag">{s}</span>' for s in req_skill_list])
                st.markdown(req_html, unsafe_allow_html=True)
            with s_col2:
                st.markdown("**Skill Gap Analysis:**")
                if missing_skills:
                    gap_html = "Missing: " + "".join([f'<span class="skill-tag-missing">{s}</span>' for s in missing_skills])
                else:
                    gap_html = '<span class="skill-tag-match">✓ Complete Skill Overlap!</span>'
                st.markdown(gap_html, unsafe_allow_html=True)

            with st.expander("📖 View Full Description"):
                st.write(job.description)
                if job.linkedin_url:
                    st.markdown(f"[Job Posting Link]({job.linkedin_url})")

            # Apply Button Action
            if job.id in existing_apps:
                app_record = existing_apps[job.id]
                st.markdown(f"✅ **Already Applied** (<span class='status-{app_record.status}'>{app_record.status.upper()}</span>)", unsafe_allow_html=True)
            else:
                if st.button(f"🚀 Apply Now (Match: {score:.1f}%)", key=f"apply_{job.id}"):
                    new_app = Application(
                        job_id=job.id,
                        candidate_id=current_user.id,
                        match_score=score,
                        status="applied"
                    )
                    db.add(new_app)
                    db.commit()
                    st.toast(f"Application submitted to {job.company}!", icon="🎉")
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        if filtered_count == 0:
            st.info("No jobs match your selected filter criteria.")

    db.close()

# -----------------------------------------------------------------------------
# PAGE: CANDIDATE - MY APPLICATIONS
# -----------------------------------------------------------------------------
elif nav_option == "📋 My Applications" and st.session_state["user"]:
    db = get_db()
    current_user_id = st.session_state["user"]["id"]
    applications = db.query(Application).filter(Application.candidate_id == current_user_id).order_by(Application.applied_at.desc()).all()

    st.markdown('<h1 class="header-title">📋 My Job Applications</h1>', unsafe_allow_html=True)
    
    if not applications:
        st.info("You haven't applied to any jobs yet. Check out the AI Recommendations tab!")
    else:
        for app in applications:
            job = app.job
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {job.title}")
                st.write(f"**🏢 {job.company}** | 📍 {job.location}")
                st.caption(f"Applied on: {app.applied_at.strftime('%B %d, %Y')}")
            with col2:
                st.markdown(f"**AI Score:** `{app.match_score:.1f}%`")
            with col3:
                st.markdown(f"**Status:** <span class='status-{app.status}'>{app.status.upper()}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    db.close()

# -----------------------------------------------------------------------------
# PAGE: RECRUITER - POST NEW JOB
# -----------------------------------------------------------------------------
elif nav_option == "➕ Post New Job" and st.session_state["user"]:
    st.markdown('<h1 class="header-title">➕ Post a New Job</h1>', unsafe_allow_html=True)

    with st.form("create_job_form"):
        j_title = st.text_input("Job Title*", placeholder="e.g. Senior Machine Learning Engineer")
        j_company = st.text_input("Company Name*", placeholder="e.g. Acme AI Technologies")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            j_location = st.text_input("Location", "Remote")
        with c2:
            j_workplace = st.selectbox("Workplace Type", ["Remote", "Hybrid", "On-site"])
        with c3:
            j_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"])

        j_skills = st.text_area("Required Skills (comma-separated)*", placeholder="e.g. python, fastapi, sql, docker, scikit-learn")
        
        c4, c5, c6 = st.columns(3)
        with c4:
            j_exp = st.number_input("Required Experience (Years)", min_value=0, value=2)
        with c5:
            j_sal_min = st.number_input("Min Salary ($)", min_value=0.0, value=80000.0, step=5000.0)
        with c6:
            j_sal_max = st.number_input("Max Salary ($)", min_value=0.0, value=120000.0, step=5000.0)

        j_desc = st.text_area("Detailed Job Description*", height=200, placeholder="Describe role, responsibilities, team, and benefits...")
        j_url = st.text_input("Company / Listing URL", "")

        submit_job = st.form_submit_button("🚀 Publish Job Posting", type="primary", use_container_width=True)
        
        if submit_job:
            if not j_title or not j_company or not j_skills or not j_desc:
                st.error("Please fill in all required fields (*).")
            else:
                db = get_db()
                new_job = JobPosting(
                    title=j_title.strip(),
                    company=j_company.strip(),
                    location=j_location.strip(),
                    workplace_type=j_workplace,
                    job_type=j_type,
                    required_skills=j_skills.strip(),
                    experience_years=j_exp,
                    salary_min=j_sal_min,
                    salary_max=j_sal_max,
                    description=j_desc.strip(),
                    linkedin_url=j_url.strip(),
                    posted_by=st.session_state["user"]["id"]
                )
                db.add(new_job)
                db.commit()
                st.success(f"Job posting '{j_title}' published successfully!")
                db.close()

# -----------------------------------------------------------------------------
# PAGE: RECRUITER - MANAGE LISTINGS
# -----------------------------------------------------------------------------
elif nav_option == "💼 Manage Job Listings" and st.session_state["user"]:
    db = get_db()
    recruiter_id = st.session_state["user"]["id"]
    my_jobs = db.query(JobPosting).filter(JobPosting.posted_by == recruiter_id).order_by(JobPosting.created_at.desc()).all()

    st.markdown('<h1 class="header-title">💼 Manage Posted Jobs</h1>', unsafe_allow_html=True)
    
    if not my_jobs:
        st.info("You haven't posted any jobs yet.")
    else:
        for job in my_jobs:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {job.title}")
                st.write(f"**🏢 {job.company}** | 📍 {job.location} | 💼 {job.job_type}")
                st.caption(f"Required Skills: {job.required_skills}")
            with col2:
                applicant_count = len(job.applications)
                st.metric("Applicants", applicant_count)
            with col3:
                if st.button("🗑️ Delete Job", key=f"del_{job.id}"):
                    db.delete(job)
                    db.commit()
                    st.success("Job posting deleted.")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    db.close()

# -----------------------------------------------------------------------------
# PAGE: RECRUITER - APPLICANT RANKING
# -----------------------------------------------------------------------------
elif nav_option == "👥 Applicant Ranking" and st.session_state["user"]:
    db = get_db()
    recruiter_id = st.session_state["user"]["id"]
    my_jobs = db.query(JobPosting).filter(JobPosting.posted_by == recruiter_id).all()

    st.markdown('<h1 class="header-title">👥 Candidate Applicant Ranking</h1>', unsafe_allow_html=True)

    if not my_jobs:
        st.info("Please post a job first to view applicants.")
    else:
        selected_job_id = st.selectbox(
            "Select Job Posting to Review Applicants:",
            [j.id for j in my_jobs],
            format_func=lambda x: next(f"{j.title} at {j.company}" for j in my_jobs if j.id == x)
        )

        job = db.query(JobPosting).filter(JobPosting.id == selected_job_id).first()
        applications = db.query(Application).filter(Application.job_id == selected_job_id).all()

        if not applications:
            st.info("No candidates have applied to this position yet.")
        else:
            candidates = [app.candidate for app in applications]
            # Rank candidates using AI Job Matcher
            ranked_candidate_pairs = ai_matcher.rank_candidates_for_job(job, candidates)

            st.write(f"Showing **{len(ranked_candidate_pairs)}** applicants ranked by AI Match Score:")

            for candidate, score in ranked_candidate_pairs:
                app_record = next(a for a in applications if a.candidate_id == candidate.id)

                st.markdown('<div class="css-card">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([3, 1, 1.2])

                with col1:
                    st.markdown(f"### 👤 {candidate.full_name}")
                    st.write(f"📧 **{candidate.email}** | 📍 {candidate.location or 'N/A'} | ⏳ {candidate.experience_years or 0} yrs exp")
                    if candidate.headline:
                        st.caption(f"Headline: {candidate.headline}")
                    st.markdown(f"**Skills:** `{candidate.skills or 'None listed'}`")

                with col2:
                    st.markdown(render_match_badge(score), unsafe_allow_html=True)

                with col3:
                    st.markdown(f"Current Status: <span class='status-{app_record.status}'>{app_record.status.upper()}</span>", unsafe_allow_html=True)
                    new_status = st.selectbox(
                        "Update Status",
                        ["applied", "shortlisted", "hired", "rejected"],
                        index=["applied", "shortlisted", "hired", "rejected"].index(app_record.status),
                        key=f"status_sel_{app_record.id}"
                    )
                    if new_status != app_record.status:
                        app_record.status = new_status
                        db.commit()
                        st.success(f"Updated status for {candidate.full_name}")
                        st.rerun()

                with st.expander("📄 View Candidate Resume & Skill Gap"):
                    missing = ai_matcher.skill_gap(candidate.skills or "", job.required_skills)
                    st.markdown(f"**Missing Required Skills:** {', '.join(missing) if missing else 'None! Complete overlap.'}")
                    if candidate.resume_text:
                        st.text_area("Extracted Resume Text", candidate.resume_text, height=150, key=f"res_{candidate.id}")
                    else:
                        st.write("No PDF resume uploaded by candidate.")

                st.markdown('</div>', unsafe_allow_html=True)

    db.close()
