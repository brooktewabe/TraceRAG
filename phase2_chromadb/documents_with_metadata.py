"""
Phase 2 — Documents with Metadata.

In a real enterprise system, documents do not just have text.
They have metadata that enables:
  1. Departmental scoping (e.g., only HR or only IT policies).
  2. Role-based access filtering (e.g., employee vs. manager).
  3. Source tracking (file name, last updated date).
"""

DOCUMENTS = [
    {
        "id": "doc_01",
        "title": "Password Recovery",
        "department": "IT",
        "category": "security",
        "access_level": "all_employees",
        "content": (
            "Password recovery process: If you have forgotten your password, "
            "click 'Forgot Password' on the login page. Enter your registered email address "
            "and you will receive a reset link within 5 minutes. The link expires after 24 hours. "
            "Contact IT support if you do not receive the email."
        ),
    },
    {
        "id": "doc_02",
        "title": "Remote Work Policy",
        "department": "HR",
        "category": "workplace",
        "access_level": "all_employees",
        "content": (
            "Remote work policy: Employees may work from home up to 3 days per week with manager approval. "
            "You must be reachable during core hours (10:00–16:00 local time). "
            "A stable internet connection and a quiet workspace are required. "
            "VPN must be active when accessing internal systems remotely."
        ),
    },
    {
        "id": "doc_03",
        "title": "Annual Leave Policy",
        "department": "HR",
        "category": "benefits",
        "access_level": "all_employees",
        "content": (
            "Annual leave policy: Full-time employees receive 20 vacation days per year. "
            "Leave must be requested at least 2 weeks in advance via the HR portal. "
            "Unused leave can be carried over up to a maximum of 5 days. "
            "Public holidays are separate from the annual leave allowance."
        ),
    },
    {
        "id": "doc_04",
        "title": "Office Security Policy",
        "department": "Operations",
        "category": "security",
        "access_level": "all_employees",
        "content": (
            "Office security policy: All employees must wear their ID badge visibly at all times. "
            "Tailgating through secure doors is prohibited. "
            "Report any suspicious activity to building security immediately. "
            "Visitors must sign in at reception and be accompanied by an employee."
        ),
    },
    {
        "id": "doc_05",
        "title": "Expense Reimbursement",
        "department": "Finance",
        "category": "expenses",
        "access_level": "all_employees",
        "content": (
            "Expense reimbursement: Submit receipts within 30 days of purchase via the finance portal. "
            "Meals are reimbursed up to $50 per day. Travel must be pre-approved for amounts over $500. "
            "Personal expenses will not be reimbursed. Receipts are required for all claims above $25."
        ),
    },
    {
        "id": "doc_06",
        "title": "IT Equipment Request",
        "department": "IT",
        "category": "hardware",
        "access_level": "all_employees",
        "content": (
            "IT equipment request: To request a new laptop, monitor, or peripheral device, "
            "submit a ticket through the IT helpdesk portal. Standard equipment is delivered within 3 business days. "
            "Specialised hardware may take up to 2 weeks. Returned equipment must be wiped before handover."
        ),
    },
    {
        "id": "doc_07",
        "title": "Onboarding Checklist",
        "department": "HR",
        "category": "workplace",
        "access_level": "all_employees",
        "content": (
            "New employee onboarding: Complete your profile in the HR system on day one. "
            "Attend the company orientation session in your first week. "
            "Your manager will assign a buddy to help you settle in. "
            "Access to systems is granted based on your role; contact IT if access is missing."
        ),
    },
    {
        "id": "doc_08",
        "title": "Code of Conduct",
        "department": "Legal",
        "category": "compliance",
        "access_level": "all_employees",
        "content": (
            "Code of conduct: All employees are expected to treat colleagues with respect and professionalism. "
            "Harassment, discrimination, and bullying are strictly prohibited. "
            "Report concerns to HR or use the anonymous ethics hotline. "
            "Violations may result in disciplinary action up to and including termination."
        ),
    },
    {
        "id": "doc_09",
        "title": "Data Privacy Policy",
        "department": "Legal",
        "category": "compliance",
        "access_level": "all_employees",
        "content": (
            "Data privacy policy: Employee and customer data must be handled in accordance with GDPR. "
            "Do not share personal data with third parties without written consent. "
            "Data must be stored on approved systems only. "
            "Report any suspected data breach to the privacy team within 24 hours."
        ),
    },
    {
        "id": "doc_10",
        "title": "Performance Review Process",
        "department": "HR",
        "category": "performance",
        "access_level": "all_employees",
        "content": (
            "Performance reviews: Annual reviews take place in December. "
            "Mid-year check-ins are held in June. Your manager will schedule a 1:1 review session. "
            "Self-assessment forms must be submitted one week before the review meeting. "
            "Ratings range from 1 (below expectations) to 5 (exceeds expectations)."
        ),
    },
]

