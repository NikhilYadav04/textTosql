"""
Seed script to create and populate the Construction Site Management SQLite database.
Run: python seed_database.py
"""
import sqlite3
import os
from pathlib import Path
from datetime import date, timedelta
import random

DB_DIR = Path(__file__).parent / "app" / "data"
DB_PATH = DB_DIR / "construction.db"

def create_tables(cursor):
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        client_name TEXT NOT NULL,
        budget REAL NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        status TEXT NOT NULL CHECK(status IN ('active','completed','on_hold','planning'))
    );

    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        address TEXT,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        site_manager TEXT,
        status TEXT NOT NULL CHECK(status IN ('active','completed','on_hold')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS contractors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        phone TEXT,
        specialization TEXT,
        rating REAL CHECK(rating >= 1 AND rating <= 5)
    );

    CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contractor_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        daily_wage REAL NOT NULL,
        phone TEXT,
        join_date TEXT NOT NULL,
        FOREIGN KEY (contractor_id) REFERENCES contractors(id)
    );

    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit TEXT NOT NULL,
        unit_price REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        phone TEXT,
        city TEXT NOT NULL,
        gst_number TEXT
    );

    CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL,
        site_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        delivery_date TEXT,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','delivered','cancelled','partial')),
        payment_status TEXT NOT NULL CHECK(payment_status IN ('paid','unpaid','partial')),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
        FOREIGN KEY (site_id) REFERENCES sites(id)
    );

    CREATE TABLE IF NOT EXISTS purchase_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
        FOREIGN KEY (material_id) REFERENCES materials(id)
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('labour','transport','material','equipment','misc')),
        description TEXT,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        approved_by TEXT,
        FOREIGN KEY (site_id) REFERENCES sites(id)
    );

    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        daily_rental_cost REAL NOT NULL,
        owner TEXT
    );

    CREATE TABLE IF NOT EXISTS equipment_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        site_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        total_cost REAL,
        FOREIGN KEY (equipment_id) REFERENCES equipment(id),
        FOREIGN KEY (site_id) REFERENCES sites(id)
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        site_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        assigned_worker_id INTEGER,
        status TEXT NOT NULL CHECK(status IN ('pending','in_progress','completed','overdue')),
        start_date TEXT,
        end_date TEXT,
        priority TEXT CHECK(priority IN ('low','medium','high','critical')),
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (site_id) REFERENCES sites(id),
        FOREIGN KEY (assigned_worker_id) REFERENCES workers(id)
    );

    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        inspector_name TEXT NOT NULL,
        inspection_date TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('safety','quality','structural','electrical','plumbing')),
        result TEXT NOT NULL CHECK(result IN ('pass','fail','conditional')),
        remarks TEXT,
        FOREIGN KEY (site_id) REFERENCES sites(id)
    );

    CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        worker_id INTEGER NOT NULL,
        log_date TEXT NOT NULL,
        hours_worked REAL NOT NULL,
        activity TEXT,
        remarks TEXT,
        FOREIGN KEY (site_id) REFERENCES sites(id),
        FOREIGN KEY (worker_id) REFERENCES workers(id)
    );
    """)

def seed_data(cursor):
    # --- Projects ---
    projects = [
        ('Skyline Heights Residency', 'Oberoi Realty', 45000000, '2025-01-15', '2026-06-30', 'active'),
        ('Metro Link Phase 2', 'Mumbai Metro Corp', 120000000, '2024-06-01', '2026-12-31', 'active'),
        ('Green Valley Township', 'Godrej Properties', 78000000, '2024-03-01', '2025-12-31', 'completed'),
        ('Sunrise Commercial Plaza', 'DLF Ltd', 55000000, '2025-04-01', '2027-03-31', 'active'),
        ('Heritage School Expansion', 'DAV Trust', 12000000, '2025-07-01', None, 'planning'),
    ]
    cursor.executemany("INSERT INTO projects (name,client_name,budget,start_date,end_date,status) VALUES (?,?,?,?,?,?)", projects)

    # --- Sites ---
    sites = [
        (1, 'Tower A Foundation', 'Plot 45, Andheri East', 'Mumbai', 'Maharashtra', 'Rajesh Patil', 'active'),
        (1, 'Tower B Structure', 'Plot 46, Andheri East', 'Mumbai', 'Maharashtra', 'Sunil Deshmukh', 'active'),
        (2, 'Tunnel Section 3', 'Aarey Colony Stretch', 'Mumbai', 'Maharashtra', 'Vikram Mehta', 'active'),
        (2, 'Station Platform BKC', 'BKC Junction', 'Mumbai', 'Maharashtra', 'Amit Joshi', 'active'),
        (2, 'Depot Construction', 'Charkop Depot Area', 'Mumbai', 'Maharashtra', 'Priya Sharma', 'on_hold'),
        (3, 'Block A Finishing', 'Sector 15, Panvel', 'Navi Mumbai', 'Maharashtra', 'Deepak Kulkarni', 'completed'),
        (3, 'Block B Finishing', 'Sector 15, Panvel', 'Navi Mumbai', 'Maharashtra', 'Meena Iyer', 'completed'),
        (3, 'Club House', 'Sector 15, Panvel', 'Navi Mumbai', 'Maharashtra', 'Deepak Kulkarni', 'completed'),
        (4, 'Ground Floor Retail', 'Cyber City, Phase 3', 'Gurugram', 'Haryana', 'Sandeep Rana', 'active'),
        (4, 'Basement Parking', 'Cyber City, Phase 3', 'Gurugram', 'Haryana', 'Kavita Nair', 'active'),
        (5, 'New Wing Foundation', 'Vasant Kunj', 'Delhi', 'Delhi', 'Rohit Verma', 'on_hold'),
        (5, 'Auditorium Block', 'Vasant Kunj', 'Delhi', 'Delhi', 'Rohit Verma', 'on_hold'),
    ]
    cursor.executemany("INSERT INTO sites (project_id,name,address,city,state,site_manager,status) VALUES (?,?,?,?,?,?,?)", sites)

    # --- Contractors ---
    contractors = [
        ('Sharma Construction Co.', 'Ramesh Sharma', '9876543210', 'Civil Works', 4.2),
        ('Gupta Electricals', 'Anil Gupta', '9876543211', 'Electrical', 3.8),
        ('Singh Steel Works', 'Harpreet Singh', '9876543212', 'Structural Steel', 4.5),
        ('Patel Plumbing Services', 'Mahesh Patel', '9876543213', 'Plumbing', 3.5),
        ('Khan Interiors', 'Irfan Khan', '9876543214', 'Interior Finishing', 4.0),
        ('Reddy Earth Movers', 'Venkat Reddy', '9876543215', 'Excavation', 4.7),
        ('Das Painting Works', 'Subhash Das', '9876543216', 'Painting', 3.9),
        ('Jain Waterproofing', 'Rakesh Jain', '9876543217', 'Waterproofing', 4.1),
    ]
    cursor.executemany("INSERT INTO contractors (company_name,contact_person,phone,specialization,rating) VALUES (?,?,?,?,?)", contractors)

    # --- Workers ---
    workers = [
        (1,'Raju Kumar','Mason',800,'9111111001','2024-01-10'),
        (1,'Suresh Yadav','Mason',800,'9111111002','2024-01-10'),
        (1,'Mohan Lal','Helper',500,'9111111003','2024-02-15'),
        (1,'Gopal Singh','Foreman',1200,'9111111004','2024-01-10'),
        (1,'Dinesh Prasad','Mason',850,'9111111005','2024-03-01'),
        (2,'Vijay Kumar','Electrician',1000,'9111111006','2024-06-01'),
        (2,'Arun Sharma','Electrician',1000,'9111111007','2024-06-01'),
        (2,'Rakesh Tiwari','Helper',500,'9111111008','2024-07-01'),
        (3,'Balwinder Singh','Welder',1100,'9111111009','2024-03-01'),
        (3,'Jaspal Kaur','Welder',1100,'9111111010','2024-03-01'),
        (3,'Gurpreet Singh','Fitter',950,'9111111011','2024-04-01'),
        (3,'Manpreet Kaur','Helper',500,'9111111012','2024-04-01'),
        (4,'Kiran Patel','Plumber',900,'9111111013','2024-06-15'),
        (4,'Sanjay Patel','Plumber',900,'9111111014','2024-06-15'),
        (4,'Bhavesh Modi','Helper',500,'9111111015','2024-07-01'),
        (5,'Salim Sheikh','Carpenter',950,'9111111016','2025-01-10'),
        (5,'Farhan Ali','Carpenter',950,'9111111017','2025-01-10'),
        (5,'Imran Khan','Painter',800,'9111111018','2025-02-01'),
        (6,'Lakshmi Reddy','Excavator Operator',1500,'9111111019','2024-01-15'),
        (6,'Ramaiah Goud','Driver',900,'9111111020','2024-01-15'),
        (6,'Srinivas Rao','Helper',500,'9111111021','2024-02-01'),
        (7,'Anup Das','Painter',850,'9111111022','2025-01-01'),
        (7,'Bikash Roy','Painter',850,'9111111023','2025-01-01'),
        (7,'Tapan Ghosh','Helper',500,'9111111024','2025-02-01'),
        (8,'Sunil Jain','Waterproofer',1000,'9111111025','2024-08-01'),
        (8,'Manoj Agarwal','Waterproofer',1000,'9111111026','2024-08-01'),
    ]
    cursor.executemany("INSERT INTO workers (contractor_id,name,role,daily_wage,phone,join_date) VALUES (?,?,?,?,?,?)", workers)

    # --- Materials ---
    materials = [
        ('OPC Cement 53 Grade','Cement','bag',380),
        ('PPC Cement','Cement','bag',350),
        ('TMT Steel Bar 12mm','Steel','kg',72),
        ('TMT Steel Bar 16mm','Steel','kg',70),
        ('River Sand','Aggregate','cubic_ft',55),
        ('M-Sand','Aggregate','cubic_ft',45),
        ('Crushed Stone 20mm','Aggregate','cubic_ft',38),
        ('Red Clay Bricks','Bricks','piece',9),
        ('AAC Blocks','Bricks','piece',55),
        ('Plywood 18mm','Wood','sheet',1800),
        ('Teak Wood','Wood','cubic_ft',3500),
        ('Emulsion Paint','Paint','litre',280),
        ('Exterior Paint','Paint','litre',420),
        ('PVC Pipe 4 inch','Plumbing','piece',350),
        ('CPVC Pipe 1 inch','Plumbing','piece',180),
        ('Copper Wire 2.5mm','Electrical','metre',28),
        ('MCB Switch 32A','Electrical','piece',320),
        ('Waterproofing Membrane','Waterproofing','sq_metre',150),
        ('Tiles 2x2 Vitrified','Flooring','sq_ft',65),
        ('Granite Slab','Flooring','sq_ft',120),
    ]
    cursor.executemany("INSERT INTO materials (name,category,unit,unit_price) VALUES (?,?,?,?)", materials)

    # --- Suppliers ---
    suppliers = [
        ('UltraTech Cement Dealers','Rajiv Mehta','9222222001','Mumbai','27AABCU9603R1ZM'),
        ('Tata Steel Distributors','Anand Tata','9222222002','Mumbai','27AAACT2727Q1ZW'),
        ('Shree Aggregates','Prakash Shinde','9222222003','Navi Mumbai','27AADCS1234P1ZQ'),
        ('Delhi Bricks & Blocks','Naresh Goel','9222222004','Delhi','07AABCD5678R1ZT'),
        ('Karnataka Timber Mart','Suresh Gowda','9222222005','Bangalore','29AABCT9012S1ZV'),
        ('Asian Paints Depot','Vivek Chauhan','9222222006','Gurugram','06AABCA3456T1ZX'),
        ('Supreme Pipes Center','Dinesh Agarwal','9222222007','Pune','27AABCS7890U1ZY'),
        ('Polycab Wire House','Manoj Kapoor','9222222008','Delhi','07AABCP1234V1ZZ'),
        ('Pidilite Waterproofing','Sanjay Bhatt','9222222009','Mumbai','27AABCP5678W1ZA'),
        ('Kajaria Tiles Showroom','Amit Singhal','9222222010','Gurugram','06AABCK9012X1ZB'),
    ]
    cursor.executemany("INSERT INTO suppliers (company_name,contact_person,phone,city,gst_number) VALUES (?,?,?,?,?)", suppliers)

    # --- Purchase Orders ---
    random.seed(42)
    base = date(2025, 1, 1)
    po_data = []
    po_item_data = []
    po_id = 1
    site_ids = list(range(1, 11))  # active/completed sites only
    for i in range(30):
        sup_id = random.randint(1, 10)
        s_id = random.choice(site_ids)
        od = base + timedelta(days=random.randint(0, 500))
        dd = od + timedelta(days=random.randint(5, 30))
        status = random.choice(['pending','delivered','delivered','delivered','partial'])
        pay = random.choice(['paid','paid','unpaid','partial'])

        # Generate 2-4 items for this PO
        num_items = random.randint(2, 4)
        total = 0
        for _ in range(num_items):
            mat_id = random.randint(1, 20)
            qty = random.randint(10, 500)
            # Fetch unit price from materials list
            up = materials[mat_id - 1][3]
            tp = round(qty * up, 2)
            total += tp
            po_item_data.append((po_id, mat_id, qty, up, tp))

        po_data.append((sup_id, s_id, od.isoformat(), dd.isoformat(), round(total, 2), status, pay))
        po_id += 1

    cursor.executemany("INSERT INTO purchase_orders (supplier_id,site_id,order_date,delivery_date,total_amount,status,payment_status) VALUES (?,?,?,?,?,?,?)", po_data)
    cursor.executemany("INSERT INTO purchase_order_items (po_id,material_id,quantity,unit_price,total_price) VALUES (?,?,?,?,?)", po_item_data)

    # --- Expenses ---
    exp_data = []
    categories = ['labour','transport','material','equipment','misc']
    descriptions = {
        'labour': ['Daily wages payment','Overtime payment','Bonus payment','Weekly settlement'],
        'transport': ['Material delivery charges','Equipment transport','Worker pickup van','Debris removal'],
        'material': ['Emergency cement purchase','Additional steel rods','Miscellaneous hardware','Safety gear purchase'],
        'equipment': ['Crane rental','Generator fuel','Mixer maintenance','Scaffolding rental'],
        'misc': ['Site office electricity','Water tanker','Tea & refreshments','First aid supplies'],
    }
    approvers = ['Rajesh Patil','Sunil Deshmukh','Vikram Mehta','Amit Joshi','Sandeep Rana']
    for i in range(50):
        s_id = random.choice(site_ids)
        cat = random.choice(categories)
        desc = random.choice(descriptions[cat])
        amt = round(random.uniform(2000, 150000), 2)
        ed = (base + timedelta(days=random.randint(0, 500))).isoformat()
        appr = random.choice(approvers)
        exp_data.append((s_id, cat, desc, amt, ed, appr))
    cursor.executemany("INSERT INTO expenses (site_id,category,description,amount,expense_date,approved_by) VALUES (?,?,?,?,?,?)", exp_data)

    # --- Equipment ---
    equipment_list = [
        ('Tower Crane TC-5010','Crane',15000,'Reddy Earth Movers'),
        ('Mobile Crane 25T','Crane',12000,'Reddy Earth Movers'),
        ('JCB 3DX Backhoe','Excavator',8000,'Reddy Earth Movers'),
        ('Hitachi EX-200','Excavator',10000,'External Rental'),
        ('Concrete Mixer 10/7','Mixer',2500,'Sharma Construction'),
        ('Concrete Mixer 16/12','Mixer',3500,'Sharma Construction'),
        ('Bar Bending Machine','Steel Work',1500,'Singh Steel Works'),
        ('Bar Cutting Machine','Steel Work',1200,'Singh Steel Works'),
        ('Diesel Generator 125kVA','Power',4000,'External Rental'),
        ('Diesel Generator 62.5kVA','Power',2500,'External Rental'),
        ('Concrete Pump Truck','Pump',18000,'External Rental'),
        ('Scaffolding Set 100sqm','Safety',1000,'Sharma Construction'),
        ('Passenger Hoist','Hoist',5000,'External Rental'),
        ('Vibrator Needle 40mm','Compaction',800,'Sharma Construction'),
        ('Transit Mixer 6cum','Mixer',7000,'External Rental'),
    ]
    cursor.executemany("INSERT INTO equipment (name,type,daily_rental_cost,owner) VALUES (?,?,?,?)", equipment_list)

    # --- Equipment Assignments ---
    eq_assign = []
    for i in range(25):
        eq_id = random.randint(1, 15)
        s_id = random.choice(site_ids)
        sd = base + timedelta(days=random.randint(0, 400))
        duration = random.randint(10, 90)
        ed = sd + timedelta(days=duration)
        cost = round(equipment_list[eq_id-1][2] * duration, 2)
        eq_assign.append((eq_id, s_id, sd.isoformat(), ed.isoformat(), cost))
    cursor.executemany("INSERT INTO equipment_assignments (equipment_id,site_id,start_date,end_date,total_cost) VALUES (?,?,?,?,?)", eq_assign)

    # --- Tasks ---
    task_names = [
        'Site Clearing','Foundation Excavation','PCC Laying','RCC Foundation',
        'Column Casting','Beam Casting','Slab Casting','Brickwork',
        'Plastering','Electrical Wiring','Plumbing Rough-in','Waterproofing',
        'Flooring Installation','Painting Interior','Painting Exterior',
        'Window Installation','Door Installation','False Ceiling',
        'Landscaping','Final Inspection Prep',
    ]
    task_data = []
    statuses = ['pending','in_progress','completed','completed','overdue']
    priorities = ['low','medium','medium','high','critical']
    worker_ids = list(range(1, 27))
    for i in range(35):
        p_id = random.randint(1, 5)
        s_id = random.choice(site_ids)
        tn = random.choice(task_names)
        w_id = random.choice(worker_ids)
        st = random.choice(statuses)
        sd = (base + timedelta(days=random.randint(0, 300))).isoformat()
        ed_val = (base + timedelta(days=random.randint(301, 550))).isoformat() if st != 'pending' else None
        pri = random.choice(priorities)
        task_data.append((p_id, s_id, tn, w_id, st, sd, ed_val, pri))
    cursor.executemany("INSERT INTO tasks (project_id,site_id,name,assigned_worker_id,status,start_date,end_date,priority) VALUES (?,?,?,?,?,?,?,?)", task_data)

    # --- Inspections ---
    insp_types = ['safety','quality','structural','electrical','plumbing']
    insp_results = ['pass','pass','pass','fail','conditional']
    inspectors = ['R.K. Verma','S.N. Gupta','Dr. A. Rao','M.S. Pillai','K.L. Bhatia']
    insp_remarks = {
        'pass': ['All standards met','Compliant with IS codes','Good workmanship observed','No issues found'],
        'fail': ['Rebar spacing incorrect','Safety nets missing','Concrete mix ratio off','Fire exit blocked'],
        'conditional': ['Minor cracks to be sealed','Need additional safety signage','Rework plumbing joint #3'],
    }
    insp_data = []
    for i in range(20):
        s_id = random.choice(site_ids)
        insp = random.choice(inspectors)
        id_date = (base + timedelta(days=random.randint(0, 500))).isoformat()
        itype = random.choice(insp_types)
        result = random.choice(insp_results)
        remark = random.choice(insp_remarks[result])
        insp_data.append((s_id, insp, id_date, itype, result, remark))
    cursor.executemany("INSERT INTO inspections (site_id,inspector_name,inspection_date,type,result,remarks) VALUES (?,?,?,?,?,?)", insp_data)

    # --- Daily Logs ---
    activities = [
        'Foundation digging','Rebar tying','Concrete pouring','Brickwork level 2',
        'Electrical conduit laying','Plumbing pipe fitting','Plastering walls',
        'Tile setting','Painting prep','Waterproofing membrane application',
        'Scaffolding setup','Material unloading','Site cleanup','Formwork carpentry',
    ]
    log_data = []
    for i in range(100):
        s_id = random.choice(site_ids)
        w_id = random.choice(worker_ids)
        ld = (base + timedelta(days=random.randint(0, 500))).isoformat()
        hrs = round(random.choice([4, 6, 8, 8, 8, 9, 10, 12]), 1)
        act = random.choice(activities)
        rmk = random.choice([None, 'Good progress', 'Delayed due to rain', 'Material shortage', 'Overtime required', None, None])
        log_data.append((s_id, w_id, ld, hrs, act, rmk))
    cursor.executemany("INSERT INTO daily_logs (site_id,worker_id,log_date,hours_worked,activity,remarks) VALUES (?,?,?,?,?,?)", log_data)


def main():
    # Create data directory
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Remove existing DB if present
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("Creating tables...")
    create_tables(cursor)

    print("Seeding data...")
    seed_data(cursor)

    conn.commit()

    # Verification
    print("\n--- Verification ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    print(f"Total tables: {len(tables)}")
    for (tname,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM [{tname}]")
        count = cursor.fetchone()[0]
        print(f"  {tname}: {count} rows")

    conn.close()
    print(f"\nDatabase created at: {DB_PATH}")


if __name__ == "__main__":
    main()
