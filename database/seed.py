"""
Seed script to populate the database with realistic mock warehouse data.
Run this after creating the database to get a working demo.
"""
import random
from datetime import datetime, timedelta
from database import db
from database.models import (
    Product, Warehouse, Inventory, Order, OrderItem,
    Allocation, PickTask, PackTask, QualityCheck,
    WarehouseException, Dispatch, InventoryMovement
)

PRODUCTS_DATA = [
    # Electronics
    ("SKU-E001", "Wireless Bluetooth Headphones", "Electronics", 89.99, 15, 60, "TechSupply Co"),
    ("SKU-E002", "USB-C Charging Cable 2m", "Electronics", 12.99, 50, 200, "CableMart Ltd"),
    ("SKU-E003", "Mechanical Keyboard RGB", "Electronics", 149.99, 10, 40, "KeyTech Inc"),
    ("SKU-E004", "Wireless Optical Mouse", "Electronics", 39.99, 20, 80, "PeriphZone"),
    ("SKU-E005", "27-inch 4K Monitor", "Electronics", 499.99, 5, 20, "DisplayPro"),
    ("SKU-E006", "Laptop Stand Aluminium", "Electronics", 34.99, 25, 100, "ErgoDeskCo"),
    ("SKU-E007", "External SSD 1TB", "Electronics", 129.99, 12, 50, "StoragePlus"),
    ("SKU-E008", "Webcam 1080p HD", "Electronics", 69.99, 15, 60, "VisionTech"),
    ("SKU-E009", "Noise Cancelling Earbuds", "Electronics", 199.99, 8, 35, "SoundWave"),
    ("SKU-E010", "Smart USB Hub 7-Port", "Electronics", 44.99, 30, 120, "HubMaster"),

    # Office Supplies
    ("SKU-O001", "Premium Ballpoint Pens (Box 50)", "Office Supplies", 14.99, 40, 150, "OfficeWorld"),
    ("SKU-O002", "A4 Printing Paper (500 sheets)", "Office Supplies", 8.99, 100, 400, "PaperKing"),
    ("SKU-O003", "Stapler Heavy Duty", "Office Supplies", 19.99, 20, 80, "OfficeWorld"),
    ("SKU-O004", "Sticky Notes Multicolor Pack", "Office Supplies", 6.99, 60, 250, "NoteSupply"),
    ("SKU-O005", "Desk Organizer Bamboo", "Office Supplies", 24.99, 15, 60, "EcoDesk"),
    ("SKU-O006", "Whiteboard Markers Set", "Office Supplies", 11.99, 35, 140, "WriteMore"),
    ("SKU-O007", "Lever Arch Files (Pack 5)", "Office Supplies", 16.99, 25, 100, "FilePro"),
    ("SKU-O008", "Scissors Professional", "Office Supplies", 9.99, 20, 80, "CutRight"),

    # Furniture
    ("SKU-F001", "Ergonomic Office Chair", "Furniture", 329.99, 5, 20, "ComfortSeating"),
    ("SKU-F002", "Height Adjustable Desk", "Furniture", 549.99, 3, 12, "DesignDesk"),
    ("SKU-F003", "Filing Cabinet 4-Drawer", "Furniture", 249.99, 4, 16, "StoreSmart"),
    ("SKU-F004", "Bookshelf Industrial", "Furniture", 179.99, 6, 24, "ShelfCo"),
    ("SKU-F005", "Monitor Arm Dual", "Furniture", 89.99, 8, 32, "ArmTech"),

    # Warehouse Equipment
    ("SKU-W001", "Safety Gloves Heavy Duty (Pack 10)", "Safety", 29.99, 30, 120, "SafetyFirst"),
    ("SKU-W002", "Safety Helmet Yellow", "Safety", 24.99, 20, 80, "SafetyFirst"),
    ("SKU-W003", "High-Vis Vest (Pack 5)", "Safety", 34.99, 25, 100, "SafetyFirst"),
    ("SKU-W004", "Barcode Scanner Handheld", "Equipment", 189.99, 5, 20, "ScanTech"),
    ("SKU-W005", "Label Printer Thermal", "Equipment", 149.99, 4, 16, "PrintPro"),
    ("SKU-W006", "Packing Tape 48mm (Pack 6)", "Packaging", 11.99, 50, 200, "PackRight"),
    ("SKU-W007", "Bubble Wrap Roll 50m", "Packaging", 18.99, 20, 80, "PackRight"),
    ("SKU-W008", "Corrugated Boxes Small (Pack 25)", "Packaging", 24.99, 30, 120, "BoxWorld"),
    ("SKU-W009", "Corrugated Boxes Medium (Pack 20)", "Packaging", 29.99, 25, 100, "BoxWorld"),
    ("SKU-W010", "Corrugated Boxes Large (Pack 15)", "Packaging", 34.99, 15, 60, "BoxWorld"),

    # Networking
    ("SKU-N001", "Ethernet Cable Cat6 5m", "Networking", 9.99, 40, 160, "NetCable"),
    ("SKU-N002", "Network Switch 8-Port", "Networking", 49.99, 10, 40, "NetPro"),
    ("SKU-N003", "WiFi Router AC1200", "Networking", 79.99, 8, 32, "WifiKing"),
    ("SKU-N004", "Patch Panel 24-Port", "Networking", 69.99, 5, 20, "NetPro"),
    ("SKU-N005", "SFP Module 10G", "Networking", 39.99, 15, 60, "FiberLink"),

    # Consumables
    ("SKU-C001", "Printer Ink Cartridge Black", "Consumables", 22.99, 30, 120, "InkWorld"),
    ("SKU-C002", "Printer Ink Cartridge Color", "Consumables", 26.99, 25, 100, "InkWorld"),
    ("SKU-C003", "Toner Cartridge Black", "Consumables", 49.99, 15, 60, "TonerPro"),
    ("SKU-C004", "AA Batteries (Pack 20)", "Consumables", 12.99, 40, 160, "PowerCell"),
    ("SKU-C005", "Cleaning Wipes Electronic (Pack 50)", "Consumables", 8.99, 30, 120, "CleanTech"),

    # Tools
    ("SKU-T001", "Screwdriver Set 32-Piece", "Tools", 34.99, 10, 40, "ToolMaster"),
    ("SKU-T002", "Digital Multimeter", "Tools", 44.99, 8, 32, "TestPro"),
    ("SKU-T003", "Cable Tester RJ45", "Tools", 24.99, 10, 40, "TestPro"),
    ("SKU-T004", "Heat Gun 2000W", "Tools", 59.99, 6, 24, "HeatPro"),
    ("SKU-T005", "Label Maker Dymo", "Tools", 39.99, 8, 32, "LabelCo"),

    # Accessories
    ("SKU-A001", "Phone Case Universal Waterproof", "Accessories", 19.99, 25, 100, "CaseWorld"),
    ("SKU-A002", "Screen Protector Tempered Glass", "Accessories", 8.99, 40, 160, "ScreenShield"),
    ("SKU-A003", "Power Strip 6-Outlet Surge", "Accessories", 29.99, 20, 80, "PowerSafe"),
    ("SKU-A004", "Cable Management Kit", "Accessories", 14.99, 25, 100, "CableOrg"),
    ("SKU-A005", "Laptop Bag 15.6 inch", "Accessories", 49.99, 12, 48, "BagPro"),
]

ZONES = ["A", "B", "C", "D", "E"]
BINS = [f"{z}{r:02d}" for z in ZONES for r in range(1, 10)]

CUSTOMER_NAMES = [
    "Apex Technologies Ltd", "Metro Office Solutions", "CloudTech Systems",
    "DataBridge Corp", "Nexus Logistics", "Pinnacle Retail Group",
    "Summit Enterprises", "Horizon Digital", "Vertex Industries",
    "Meridian Supplies", "Zenith Commerce", "Orion Tech Hub",
    "Falcon Distribution", "Atlas Wholesale", "Titan Resources",
    "Nova Office Park", "Sterling Solutions", "Cobalt Industries",
    "Phoenix Enterprises", "Matrix Supply Chain"
]

WORKERS = [
    "James Carter", "Sarah Mitchell", "David Park", "Emily Rodriguez",
    "Marcus Johnson", "Linda Chen", "Alex Thompson", "Priya Patel",
    "Ben Wilson", "Rachel Adams"
]

CARRIERS = ["FedEx", "UPS", "DHL", "Royal Mail", "Hermes", "DPD"]


def seed_database():
    """Populate the database with realistic mock data."""
    print("[INFO] Starting database seed...")

    # Clear existing data
    InventoryMovement.query.delete()
    Dispatch.query.delete()
    QualityCheck.query.delete()
    PackTask.query.delete()
    PickTask.query.delete()
    WarehouseException.query.delete()
    Allocation.query.delete()
    OrderItem.query.delete()
    Order.query.delete()
    Inventory.query.delete()
    Warehouse.query.delete()
    Product.query.delete()
    db.session.commit()

    # ── 1. WAREHOUSES ──────────────────────────────────────────────────────────
    wh1 = Warehouse(
        name="WareMind Central Hub",
        location="Birmingham, UK - Industrial Estate North",
        capacity=50000,
        status="ACTIVE",
    )
    wh2 = Warehouse(
        name="WareMind South Depot",
        location="London, UK - Logistics Park East",
        capacity=30000,
        status="ACTIVE",
    )
    db.session.add_all([wh1, wh2])
    db.session.flush()
    print(f"  [+] Created 2 warehouses")
    # ── 2. PRODUCTS ────────────────────────────────────────────────────────────
    PRODUCT_IMAGES = {
        "SKU-E001": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200&q=80",
        "SKU-E002": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=200&q=80",
        "SKU-E003": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=200&q=80",
        "SKU-E004": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=200&q=80",
        "SKU-E005": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=200&q=80",
        "SKU-E006": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=200&q=80",
        "SKU-E007": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=200&q=80",
        "SKU-E008": "https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=200&q=80",
        "SKU-E009": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=200&q=80",
        "SKU-E010": "https://images.unsplash.com/photo-1616440342855-467f781df0bb?w=200&q=80",
        "SKU-F001": "https://images.unsplash.com/photo-1580481072645-022f9a6d505b?w=200&q=80",
        "SKU-F002": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=200&q=80",
        "SKU-W002": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=200&q=80",
        "SKU-W004": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=200&q=80",
        "SKU-N003": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=200&q=80",
    }
    CATEGORY_FALLBACK_IMAGES = {
        "Electronics": "https://images.unsplash.com/photo-1498049860654-af1a5c566876?w=200&q=80",
        "Office Supplies": "https://images.unsplash.com/photo-1456735190827-d1262f71b8a3?w=200&q=80",
        "Furniture": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=200&q=80",
        "Safety": "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=200&q=80",
        "Equipment": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=200&q=80",
        "Packaging": "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=200&q=80",
        "Networking": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=200&q=80",
        "Consumables": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80",
        "Tools": "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=200&q=80",
        "Accessories": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200&q=80",
    }

    products = []
    for sku, name, cat, price, reorder_lv, reorder_qty, supplier in PRODUCTS_DATA:
        img_url = PRODUCT_IMAGES.get(sku, CATEGORY_FALLBACK_IMAGES.get(cat, "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80"))
        p = Product(
            sku=sku, name=name, category=cat, price=price,
            reorder_level=reorder_lv, reorder_quantity=reorder_qty,
            supplier=supplier, image_url=img_url,
            description=f"High-quality {name.lower()} sourced from {supplier}.",
        )
        products.append(p)
        db.session.add(p)
    db.session.flush()
    print(f"  [+] Created {len(products)} products with image URLs")

    # ── 3. INVENTORY ───────────────────────────────────────────────────────────
    inventory_records = []
    now = datetime.utcnow()

    # Define stock scenarios for first 10 products (electronics) to demo different states
    stock_scenarios = {
        0: ("healthy",  150, 10, 2),   # Healthy stock
        1: ("low",       18,  5, 1),   # Low stock (near reorder level)
        2: ("critical",   6,  2, 0),   # Critical low
        3: ("healthy",   95, 15, 3),   # Healthy
        4: ("out",        0,  0, 0),   # Out of stock
        5: ("healthy",  200,  5, 1),   # Overstock
        6: ("low",       14,  4, 2),   # Low stock
        7: ("healthy",   80, 10, 0),   # Healthy
        8: ("damaged",   40, 10, 15),  # High damage
        9: ("low",       22,  8, 1),   # Low stock
    }

    for i, product in enumerate(products):
        # Each product gets inventory in at least one warehouse
        warehouses_for_product = [wh1] if i % 3 != 0 else [wh1, wh2]

        for wh_idx, wh in enumerate(warehouses_for_product):
            zone = random.choice(ZONES)
            bin_loc = f"{zone}-{random.randint(1, 20):02d}"

            if i in stock_scenarios and wh_idx == 0:
                _, qty, reserved, damaged = stock_scenarios[i]
            else:
                qty = random.randint(20, 200)
                reserved = random.randint(0, min(20, qty // 4))
                damaged = random.randint(0, min(5, qty // 20))

            inv = Inventory(
                product_id=product.id,
                warehouse_id=wh.id,
                zone=zone,
                bin_location=bin_loc,
                quantity=qty,
                reserved_quantity=reserved,
                damaged_quantity=damaged,
                last_updated=now - timedelta(minutes=random.randint(5, 500)),
            )
            inventory_records.append(inv)
            db.session.add(inv)

    db.session.flush()
    print(f"  [+] Created {len(inventory_records)} inventory records")

    # ── 4. ORDERS ──────────────────────────────────────────────────────────────
    order_configs = [
        # (customer_type, priority, status, hours_until_deadline, days_ago_created)
        ("PREMIUM",   "CRITICAL", "PICKING",          2,  0),
        ("PREMIUM",   "CRITICAL", "ALLOCATED",         3,  0),
        ("PREMIUM",   "HIGH",     "PACKING",           5,  1),
        ("STANDARD",  "HIGH",     "QUALITY_CHECK",     8,  1),
        ("PREMIUM",   "CRITICAL", "EXCEPTION",         1,  0),
        ("WHOLESALE", "HIGH",     "ALLOCATED",        12,  1),
        ("STANDARD",  "NORMAL",   "PICKING",          24,  2),
        ("STANDARD",  "NORMAL",   "PACKING",          20,  2),
        ("WHOLESALE", "NORMAL",   "CREATED",          36,  0),
        ("STANDARD",  "LOW",      "CREATED",          48,  3),
        ("PREMIUM",   "HIGH",     "READY_TO_DISPATCH", 6,  2),
        ("STANDARD",  "NORMAL",   "DISPATCHED",       24,  3),
        ("PREMIUM",   "CRITICAL", "ALLOCATED",         4,  0),
        ("WHOLESALE", "NORMAL",   "PICKING",          30,  2),
        ("STANDARD",  "HIGH",     "EXCEPTION",         6,  1),
        ("STANDARD",  "LOW",      "COMPLETED",        72,  5),
        ("PREMIUM",   "HIGH",     "QUALITY_CHECK",     9,  2),
        ("WHOLESALE", "NORMAL",   "PACKING",          18,  1),
        ("STANDARD",  "NORMAL",   "ALLOCATED",        40,  1),
        ("PREMIUM",   "CRITICAL", "PICKING",           5,  0),
        ("STANDARD",  "LOW",      "CREATED",          60,  0),
        ("WHOLESALE", "HIGH",     "DISPATCHED",       24,  4),
        ("STANDARD",  "NORMAL",   "COMPLETED",        72,  6),
        ("PREMIUM",   "HIGH",     "ALLOCATED",        10,  1),
        ("STANDARD",  "NORMAL",   "PICKING",          28,  2),
        ("WHOLESALE", "LOW",      "CREATED",          96,  1),
        ("STANDARD",  "HIGH",     "PACKING",          15,  2),
        ("PREMIUM",   "CRITICAL", "EXCEPTION",         2,  0),
        ("STANDARD",  "NORMAL",   "QUALITY_CHECK",    20,  3),
        ("WHOLESALE", "HIGH",     "READY_TO_DISPATCH", 8,  2),
        ("STANDARD",  "LOW",      "COMPLETED",        48,  7),
        ("PREMIUM",   "HIGH",     "DISPATCHED",       12,  3),
        ("STANDARD",  "NORMAL",   "ALLOCATED",        32,  1),
        ("WHOLESALE", "NORMAL",   "PICKING",          24,  2),
        ("STANDARD",  "HIGH",     "PACKING",          10,  1),
    ]

    priority_scores = {
        "CRITICAL": random.uniform(82, 99),
        "HIGH":     random.uniform(62, 79),
        "NORMAL":   random.uniform(42, 59),
        "LOW":      random.uniform(15, 38),
    }

    priority_reasons = {
        "CRITICAL": (
            "Priority Score: {score:.0f} — Critical priority because delivery deadline "
            "is within {hours} hours, customer is {ctype}, and order value exceeds threshold."
        ),
        "HIGH": (
            "Priority Score: {score:.0f} — High priority due to {ctype} customer status "
            "and delivery deadline within {hours} hours."
        ),
        "NORMAL": (
            "Priority Score: {score:.0f} — Normal priority. Standard customer with "
            "deadline in {hours} hours."
        ),
        "LOW": (
            "Priority Score: {score:.0f} — Low priority. Deadline is not imminent "
            "({hours} hours remaining). Standard processing applies."
        ),
    }

    orders = []
    for idx, (ctype, priority, status, hours, days_ago) in enumerate(order_configs):
        score = random.uniform(
            {"CRITICAL": 82, "HIGH": 62, "NORMAL": 42, "LOW": 15}[priority],
            {"CRITICAL": 99, "HIGH": 79, "NORMAL": 59, "LOW": 38}[priority],
        )
        reason = priority_reasons[priority].format(
            score=score, hours=hours, ctype=ctype.lower()
        )
        created = now - timedelta(days=days_ago, hours=random.randint(0, 6))
        deadline = now + timedelta(hours=hours)
        customer = random.choice(CUSTOMER_NAMES)

        order = Order(
            order_number=f"ORD-{5000 + idx + 1:04d}",
            customer_name=customer,
            customer_type=ctype,
            priority=priority,
            priority_score=round(score, 1),
            priority_reason=reason,
            status=status,
            deadline=deadline,
            created_at=created,
            updated_at=created + timedelta(hours=random.randint(0, 3)),
        )
        orders.append(order)
        db.session.add(order)

    db.session.flush()
    print(f"  [+] Created {len(orders)} orders")

    # ── 5. ORDER ITEMS ─────────────────────────────────────────────────────────
    all_inv = inventory_records
    order_items_created = 0

    for order in orders:
        num_items = random.randint(1, 5)
        chosen_prods = random.sample(products, min(num_items, len(products)))
        for prod in chosen_prods:
            qty = random.randint(1, 15)
            # Determine allocated/picked/packed based on status
            alloc_qty = picked_qty = packed_qty = 0
            if order.status in ["ALLOCATED", "PICKING", "PACKING", "QUALITY_CHECK",
                                 "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]:
                alloc_qty = min(qty, qty - random.randint(0, 2))
            if order.status in ["PICKING", "PACKING", "QUALITY_CHECK",
                                 "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]:
                picked_qty = alloc_qty
            if order.status in ["PACKING", "QUALITY_CHECK",
                                 "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]:
                packed_qty = picked_qty

            oi = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=qty,
                allocated_quantity=alloc_qty,
                picked_quantity=picked_qty,
                packed_quantity=packed_qty,
            )
            db.session.add(oi)
            order_items_created += 1

    db.session.flush()
    print(f"  [+] Created {order_items_created} order items")

    # ── 6. ALLOCATIONS ─────────────────────────────────────────────────────────
    alloc_statuses = ["ALLOCATED", "PICKING", "PACKING", "QUALITY_CHECK",
                      "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]
    alloc_count = 0

    for order in orders:
        if order.status in alloc_statuses:
            for item in order.items:
                # Find inventory for this product
                inv_for_prod = [i for i in inventory_records
                                if i.product_id == item.product_id]
                if not inv_for_prod:
                    continue
                inv = inv_for_prod[0]
                status_val = "ALLOCATED" if item.allocated_quantity >= item.quantity else "PARTIAL"
                alloc = Allocation(
                    order_id=order.id,
                    product_id=item.product_id,
                    inventory_id=inv.id,
                    requested_quantity=item.quantity,
                    allocated_quantity=item.allocated_quantity,
                    status=status_val,
                    reason=f"Auto-allocated from {inv.zone}-{inv.bin_location}",
                    created_at=order.created_at + timedelta(minutes=random.randint(5, 30)),
                )
                db.session.add(alloc)
                alloc_count += 1

    db.session.flush()
    print(f"  [+] Created {alloc_count} allocations")

    # ── 7. PICK TASKS ──────────────────────────────────────────────────────────
    pick_count = 0
    pick_statuses = ["PICKING", "PACKING", "QUALITY_CHECK",
                     "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]

    for order in orders:
        if order.status in pick_statuses:
            worker = random.choice(WORKERS)
            for seq, item in enumerate(order.items, 1):
                inv_for_prod = [i for i in inventory_records
                                if i.product_id == item.product_id]
                if not inv_for_prod:
                    continue
                inv = inv_for_prod[0]
                pt_status = "COMPLETED" if order.status != "PICKING" else "IN_PROGRESS"
                started = order.updated_at + timedelta(minutes=random.randint(10, 40))
                completed = started + timedelta(minutes=random.randint(5, 20)) if pt_status == "COMPLETED" else None
                pt = PickTask(
                    order_id=order.id,
                    product_id=item.product_id,
                    worker_name=worker,
                    zone=inv.zone,
                    bin_location=inv.bin_location,
                    quantity=item.picked_quantity or item.quantity,
                    sequence=seq,
                    status=pt_status,
                    started_at=started,
                    completed_at=completed,
                )
                db.session.add(pt)
                pick_count += 1

    db.session.flush()
    print(f"  [+] Created {pick_count} pick tasks")

    # ── 8. PACK TASKS ──────────────────────────────────────────────────────────
    pack_statuses = ["PACKING", "QUALITY_CHECK", "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]
    pack_count = 0
    stations = ["PS-01", "PS-02", "PS-03", "PS-04"]

    for order in orders:
        if order.status in pack_statuses:
            worker = random.choice(WORKERS)
            pt_status = "COMPLETED" if order.status != "PACKING" else "IN_PROGRESS"
            started = order.updated_at + timedelta(minutes=random.randint(30, 60))
            completed = started + timedelta(minutes=random.randint(10, 30)) if pt_status == "COMPLETED" else None
            pkt = PackTask(
                order_id=order.id,
                packing_station=random.choice(stations),
                worker_name=worker,
                status=pt_status,
                started_at=started,
                completed_at=completed,
            )
            db.session.add(pkt)
            pack_count += 1

    db.session.flush()
    print(f"  [+] Created {pack_count} pack tasks")

    # ── 9. QUALITY CHECKS ──────────────────────────────────────────────────────
    qc_statuses = ["QUALITY_CHECK", "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]
    qc_count = 0

    for order in orders:
        if order.status in qc_statuses:
            qc_status = "PASSED" if order.status != "QUALITY_CHECK" else "PENDING"
            damaged = random.randint(0, 1) if random.random() < 0.1 else 0
            missing = random.randint(0, 1) if random.random() < 0.05 else 0
            if damaged > 0 or missing > 0:
                qc_status = "FAILED"
            checked_at = order.updated_at + timedelta(minutes=random.randint(60, 120)) if qc_status != "PENDING" else None
            qc = QualityCheck(
                order_id=order.id,
                checked_by=random.choice(WORKERS),
                status=qc_status,
                damaged_items=damaged,
                missing_items=missing,
                notes="All items verified." if qc_status == "PASSED" else "Issues found during inspection.",
                checked_at=checked_at,
            )
            db.session.add(qc)
            qc_count += 1

    db.session.flush()
    print(f"  [+] Created {qc_count} quality checks")

    # ── 10. DISPATCHES ─────────────────────────────────────────────────────────
    dispatch_statuses = ["READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"]
    dispatch_count = 0

    for order in orders:
        if order.status in dispatch_statuses:
            carrier = random.choice(CARRIERS)
            tracking = f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12))}"
            d_status = "DELIVERED" if order.status == "COMPLETED" else "IN_TRANSIT" if order.status == "DISPATCHED" else "PENDING"
            dispatch_time = order.updated_at + timedelta(hours=random.randint(1, 3)) if d_status != "PENDING" else None
            est_delivery = (dispatch_time + timedelta(days=random.randint(1, 3))) if dispatch_time else None
            disp = Dispatch(
                order_id=order.id,
                carrier=carrier,
                tracking_number=tracking,
                status=d_status,
                dispatch_time=dispatch_time,
                estimated_delivery=est_delivery,
            )
            db.session.add(disp)
            dispatch_count += 1

    db.session.flush()
    print(f"  [+] Created {dispatch_count} dispatches")

    # ── 11. EXCEPTIONS ─────────────────────────────────────────────────────────
    exception_configs = [
        # LOW_STOCK exceptions
        (None, products[1].id, "LOW_STOCK", "HIGH",
         f"Product '{products[1].name}' (SKU: {products[1].sku}) has only 18 units available, "
         f"below the reorder level of {products[1].reorder_level} units.",
         f"Initiate replenishment order for {products[1].reorder_quantity} units from "
         f"{products[1].supplier} immediately. Expected lead time: 2-3 business days.",
         "OPEN"),
        (None, products[6].id, "LOW_STOCK", "MEDIUM",
         f"Product '{products[6].name}' (SKU: {products[6].sku}) stock is critically low at "
         f"14 units with 4 reserved for pending orders.",
         f"Place emergency order for {products[6].reorder_quantity} units. "
         f"Consider reallocating stock from alternative suppliers.",
         "IN_PROGRESS"),
        (None, products[9].id, "LOW_STOCK", "MEDIUM",
         f"Product '{products[9].name}' (SKU: {products[9].sku}) approaching reorder point. "
         f"22 units on hand with 8 reserved.",
         f"Schedule routine replenishment for {products[9].reorder_quantity} units.",
         "OPEN"),

        # OUT_OF_STOCK
        (orders[4].id, products[4].id, "OUT_OF_STOCK", "CRITICAL",
         f"Product '{products[4].name}' (SKU: {products[4].sku}) is completely out of stock. "
         f"Critical order {orders[4].order_number} requires 3 units and cannot be fulfilled.",
         "Contact supplier for emergency stock. Place expedited order and update customer about delay. "
         "Consider partial fulfillment from returned/damaged stock after inspection.",
         "OPEN"),

        # ALLOCATION_CONFLICT
        (orders[1].id, products[0].id, "ALLOCATION_CONFLICT", "CRITICAL",
         f"Allocation conflict: Critical order {orders[1].order_number} requires 10 units of "
         f"'{products[0].name}' but only 7 units are available. "
         f"Normal-priority order is competing for the same stock.",
         "Prioritize allocation to critical order. Allocate available 7 units to "
         f"{orders[1].order_number}. Backorder 3 units and trigger emergency replenishment. "
         "Notify customer of partial fulfillment.",
         "OPEN"),

        # PICKING_DELAY
        (orders[0].id, None, "PICKING_DELAY", "HIGH",
         f"Order {orders[0].order_number} picking task has exceeded expected time by 35 minutes. "
         "Worker James Carter has been in Zone B for over 45 minutes.",
         "Assign additional picker to assist. Re-sequence picking route to optimize path. "
         "Check if products have been relocated without bin update.",
         "IN_PROGRESS"),

        # QUALITY_FAILURE
        (orders[14].id, products[2].id, "QUALITY_FAILURE", "HIGH",
         f"Quality check failed for order {orders[14].order_number}. 2 units of "
         f"'{products[2].name}' found damaged during inspection. Missing 1 unit.",
         "Remove damaged units from inventory. Locate replacement stock from Zone D. "
         "Re-pack order and re-run quality check. Update inventory damage records.",
         "OPEN"),

        # DAMAGED_ITEM
        (None, products[8].id, "DAMAGED_ITEM", "MEDIUM",
         f"15 units of '{products[8].name}' (SKU: {products[8].sku}) reported as damaged in "
         "Zone C, Bin C-07. Damage discovered during routine inspection.",
         "Quarantine damaged units. Initiate damage report and supplier claim. "
         "Update inventory records to reflect damaged quantity. Inspect adjacent stock.",
         "OPEN"),

        # PACKING_DELAY
        (orders[27].id, None, "PACKING_DELAY", "MEDIUM",
         f"Order {orders[27].order_number} packing is delayed. Current packing time is "
         "47 minutes vs expected 15 minutes average.",
         "Escalate to packing station supervisor. Check if station PS-02 is understaffed. "
         "Consider moving order to PS-03 which has lighter workload.",
         "OPEN"),

        # MISSING_ITEM
        (orders[3].id, products[3].id, "MISSING_ITEM", "HIGH",
         f"Order {orders[3].order_number}: 2 units of '{products[3].name}' marked as picked "
         "but cannot be found at packing station. Possible scanning error or misplacement.",
         "Conduct immediate bin search in Zone A. Review picker scan logs. "
         "If not found within 15 minutes, reallocate from nearest bin with stock.",
         "IN_PROGRESS"),
    ]

    exc_count = 0
    for order_id, prod_id, exc_type, severity, desc, rec, status in exception_configs:
        exc = WarehouseException(
            order_id=order_id,
            product_id=prod_id,
            exception_type=exc_type,
            severity=severity,
            description=desc,
            recommended_action=rec,
            status=status,
            created_at=now - timedelta(minutes=random.randint(5, 300)),
        )
        db.session.add(exc)
        exc_count += 1

    # Add some resolved exceptions from today
    resolved_types = [
        ("LOW_STOCK", "MEDIUM", products[10].id),
        ("PICKING_DELAY", "LOW", None),
        ("QUALITY_FAILURE", "MEDIUM", None),
        ("ALLOCATION_CONFLICT", "HIGH", products[3].id),
        ("OUT_OF_STOCK", "HIGH", products[5].id),
    ]
    for exc_type, severity, prod_id in resolved_types:
        exc = WarehouseException(
            order_id=None,
            product_id=prod_id,
            exception_type=exc_type,
            severity=severity,
            description=f"Resolved {exc_type.replace('_', ' ').lower()} exception.",
            recommended_action="Action was taken.",
            status="RESOLVED",
            resolution="Issue resolved by warehouse team.",
            created_at=now - timedelta(hours=random.randint(3, 10)),
            resolved_at=now - timedelta(hours=random.randint(1, 3)),
        )
        db.session.add(exc)
        exc_count += 1

    db.session.flush()
    print(f"  [+] Created {exc_count} exceptions ({len(resolved_types)} resolved today)")

    # ── 12. INVENTORY MOVEMENTS ────────────────────────────────────────────────
    mov_count = 0
    recent_movements = [
        ("ALLOCATION", "ORD-5001 allocation", products[0], inventory_records[0], 10),
        ("OUTBOUND",   "ORD-5003 dispatch",   products[2], inventory_records[2],  5),
        ("DAMAGE",     "Routine inspection",   products[8], inventory_records[8], -15),
        ("INBOUND",    "Supplier delivery from TechSupply Co", products[0], inventory_records[0], 50),
        ("ADJUSTMENT", "Cycle count correction", products[3], inventory_records[3], -2),
        ("ALLOCATION", "ORD-5012 allocation", products[6], inventory_records[6],  8),
        ("RELEASE",    "ORD-5016 cancellation", products[1], inventory_records[1],  5),
        ("OUTBOUND",   "ORD-5022 dispatch",   products[9], inventory_records[9],  3),
        ("INBOUND",    "Emergency restock from PeriphZone", products[3], inventory_records[3], 30),
        ("ALLOCATION", "ORD-5028 allocation", products[4], inventory_records[4],  2),
    ]

    for mov_type, reference, prod, inv_rec, qty in recent_movements:
        mov = InventoryMovement(
            product_id=prod.id,
            inventory_id=inv_rec.id,
            movement_type=mov_type,
            quantity=qty,
            reference=reference,
            notes=f"Recorded by warehouse system",
            created_at=now - timedelta(minutes=random.randint(2, 480)),
        )
        db.session.add(mov)
        mov_count += 1

    db.session.commit()
    print(f"  [+] Created {mov_count} inventory movements")

    print("\n[SUCCESS] Database seeded successfully!")
    print(f"   Products:            {len(products)}")
    print(f"   Warehouses:          2")
    print(f"   Inventory Records:   {len(inventory_records)}")
    print(f"   Orders:              {len(orders)}")
    print(f"   Order Items:         {order_items_created}")
    print(f"   Allocations:         {alloc_count}")
    print(f"   Pick Tasks:          {pick_count}")
    print(f"   Pack Tasks:          {pack_count}")
    print(f"   Quality Checks:      {qc_count}")
    print(f"   Dispatches:          {dispatch_count}")
    print(f"   Exceptions:          {exc_count}")
    print(f"   Inventory Movements: {mov_count}")
    print(f"   Products:            {len(products)}")
    print(f"   Warehouses:          2")
    print(f"   Inventory Records:   {len(inventory_records)}")
    print(f"   Orders:              {len(orders)}")
    print(f"   Order Items:         {order_items_created}")
    print(f"   Allocations:         {alloc_count}")
    print(f"   Pick Tasks:          {pick_count}")
    print(f"   Pack Tasks:          {pack_count}")
    print(f"   Quality Checks:      {qc_count}")
    print(f"   Dispatches:          {dispatch_count}")
    print(f"   Exceptions:          {exc_count}")
    print(f"   Inventory Movements: {mov_count}")
