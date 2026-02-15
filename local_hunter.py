from fpdf import FPDF

class ResumePDF(FPDF):
    def header(self):
        # Name
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(20, 20, 20)
        self.cell(0, 10, 'AASHIKA PANDEY', ln=True, align='C')
        
        # Contact Info
        self.set_font('Helvetica', '', 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, 'Koteshwor, Kathmandu | +977 982-4873029 | aashika100pandey@gmail.com', ln=True, align='C')
        self.cell(0, 5, 'linkedin.com/in/aashika-pandey | github.com/aashika-pandey', ln=True, align='C')
        
        # Divider
        self.ln(2)
        self.set_draw_color(50, 50, 50)
        self.line(10, 30, 200, 30)
        self.ln(4)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(235, 235, 235)  # Light Grey
        self.cell(0, 6, title.upper(), ln=True, fill=True)
        self.ln(2)

    def role_entry(self, role, org, date):
        self.set_font('Helvetica', 'B', 10)
        self.cell(125, 5, role, ln=0)
        self.set_font('Helvetica', 'I', 9)
        self.cell(0, 5, f"{org} | {date}", ln=1, align='R')

    def bullet(self, text):
        self.set_font('Helvetica', '', 9)
        self.set_x(12)
        self.multi_cell(0, 4, f"- {text}")
        self.ln(1)

# Initialize PDF
pdf = ResumePDF()
pdf.set_margins(10, 10, 10)
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=5)

# --- 1. PROFESSIONAL SUMMARY ---
pdf.section_title('PROFESSIONAL PROFILE')
profile = (
    "Innovation-driven Computer Engineering student (7th Sem) and Technical Head of necIT Club. "
    "Aspire Leaders Finalist (Harvard Faculty Training) with expertise in Causal AI, IoT, and FinTech. "
    "Proven leader with 4+ hackathon wins and research in satellite communications. "
    "Passionate about bridging the digital divide through hardware-software integration."
)
pdf.set_font('Helvetica', '', 9)
pdf.multi_cell(0, 4, profile)
pdf.ln(2)

# --- 2. GLOBAL LEADERSHIP & EXPERIENCE ---
pdf.section_title('LEADERSHIP & EXPERIENCE')

# Aspire Leaders
pdf.role_entry("Aspire Leaders Program Finalist", "Harvard Business School Faculty (Training)", "2025")
pdf.bullet("Selected as one of ~10,000 finalists from 54,000+ applicants for elite leadership training.")

# Technical Head
pdf.role_entry("Technical Head", "necIT Club (Nepal Engineering College)", "2026 - Present")
pdf.bullet("Leading technical workshops, coding competitions, and hackathons for 500+ students.")
pdf.bullet("Overseeing campus-wide software deployment and managing technical resources.")

# Code for Change
pdf.role_entry("Active Member", "Code for Change", "2024")
pdf.bullet("Contributed to high-impact digital literacy campaigns and community coding projects.")
pdf.ln(1)

# --- 3. UNPUBLISHED RESEARCH & INNOVATIONS ---
pdf.section_title('RESEARCH & TECHNICAL INNOVATIONS')

# DSCM
pdf.role_entry("Hybrid Causal-Generative Models (DSCM)", "Domain: Causal AI", "Unpublished Research")
pdf.bullet("Proposed 'DSCM' architecture to mitigate AI hallucinations by embedding structured causal graphs.")

# Satellite Comm
pdf.role_entry("Direct-to-Device (D2D) Satellite Comm", "Domain: Telecommunications", "Unpublished Paper")
pdf.bullet("Designed a blueprint for connecting smartphones directly to LEO satellites with <50ms latency.")
pdf.ln(1)

# --- 4. KEY ENGINEERING PROJECTS ---
pdf.section_title('KEY PROJECTS')

# Offline Wallet
pdf.role_entry("Offline Digital Wallet", "FinTech & Security", "2025")
pdf.bullet("Engineered a secure, offline-first payment system using AES encryption and delayed sync.")

# Smart Irrigation
pdf.role_entry("Smart Irrigation System", "IoT Hardware & Automation", "2025")
pdf.bullet("Designed an automated water supply system using soil moisture sensors and logic-gate triggers.")
pdf.bullet("Created a hardware-software feedback loop that reduced water wastage by 40%.")

# Apps
pdf.role_entry("NEC Digital App & PU Syllabus Hub", "Flutter Mobile Development", "2024 - 2025")
pdf.bullet("Developed cross-platform academic apps with real-time notifications and offline database sync.")
pdf.ln(1)

# --- 5. AWARDS & CERTIFICATIONS ---
pdf.section_title('HONORS & CERTIFICATIONS')

# Hackathons
pdf.set_font('Helvetica', 'B', 9)
pdf.cell(0, 5, "Veteran Participant of 4+ Major Hackathons (Inc. Nec Ignieum & Locus 2025)", ln=True)
pdf.set_font('Helvetica', '', 9)

# Certs List
pdf.bullet("Hardware Fellowship | Pulchowk Campus (LOCUS) - Embedded Systems Track")
pdf.bullet("Software Fellowship (2024) - Recognition for excellence in Software Engineering.")
pdf.bullet("1st Runner Up | Hult Prize (2024-2025) - Social Entrepreneurship")
pdf.bullet("Cyber Security Workshop (2024) - Network Defense & Threat Analysis")
pdf.ln(1)

# --- 6. TECHNICAL SKILLS ---
pdf.section_title('TECHNICAL ARSENAL')
pdf.set_font('Helvetica', 'B', 9)
pdf.cell(25, 5, "Languages:", ln=0)
pdf.set_font('Helvetica', '', 9)
pdf.cell(0, 5, "Python, Dart (Flutter), C, C++, SQL", ln=1)

pdf.set_font('Helvetica', 'B', 9)
pdf.cell(25, 5, "Domains:", ln=0)
pdf.set_font('Helvetica', '', 9)
pdf.cell(0, 5, "IoT, FinTech, Causal AI, Mobile App Dev, Network Security", ln=1)
pdf.ln(1)

# --- 7. EDUCATION ---
pdf.section_title('EDUCATION')

# NEC
pdf.role_entry("Bachelor in Computer Engineering", "Nepal Engineering College (nec)", "2022 - Present")

# KMC
pdf.role_entry("Secondary Education (Science)", "Kathmandu Model College", "2020 - 2022")
pdf.set_font('Helvetica', '', 9)
pdf.set_x(12)
pdf.cell(0, 4, "- Major: Biology, Physics, and Mathematics", ln=1)

# Primary (New Addition)
pdf.role_entry("Primary Education", "Veena Vidya Mandir English Boarding School", "2011 - 2020")

# Output
pdf.output('Aashika_Pandey_Full_Resume.pdf')
print("Resume Generated: Aashika_Pandey_Full_Resume.pdf")