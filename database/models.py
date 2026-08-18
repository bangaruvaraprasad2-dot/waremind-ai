from datetime import datetime
from database import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False, default=0.0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    reorder_quantity = db.Column(db.Integer, nullable=False, default=50)
    supplier = db.Column(db.String(200))
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inventory_records = db.relationship("Inventory", backref="product", lazy=True)
    order_items = db.relationship("OrderItem", backref="product", lazy=True)
    allocations = db.relationship("Allocation", backref="product", lazy=True)
    exceptions = db.relationship("WarehouseException", backref="product", lazy=True)
    movements = db.relationship("InventoryMovement", backref="product", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": self.price,
            "reorder_level": self.reorder_level,
            "reorder_quantity": self.reorder_quantity,
            "supplier": self.supplier,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(300))
    capacity = db.Column(db.Integer, default=10000)
    status = db.Column(db.String(50), default="ACTIVE")

    inventory_records = db.relationship("Inventory", backref="warehouse", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "capacity": self.capacity,
            "status": self.status,
        }


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    warehouse_id = db.Column(
        db.Integer, db.ForeignKey("warehouses.id"), nullable=False
    )
    zone = db.Column(db.String(10), nullable=False)
    bin_location = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved_quantity = db.Column(db.Integer, nullable=False, default=0)
    damaged_quantity = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    allocations = db.relationship("Allocation", backref="inventory", lazy=True)
    movements = db.relationship("InventoryMovement", backref="inventory", lazy=True)

    @property
    def available_quantity(self):
        return max(
            0, self.quantity - self.reserved_quantity - self.damaged_quantity
        )

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "zone": self.zone,
            "bin_location": self.bin_location,
            "quantity": self.quantity,
            "reserved_quantity": self.reserved_quantity,
            "damaged_quantity": self.damaged_quantity,
            "available_quantity": self.available_quantity,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_type = db.Column(
        db.String(50), default="STANDARD"
    )  # PREMIUM, STANDARD, WHOLESALE
    priority = db.Column(
        db.String(20), default="NORMAL"
    )  # CRITICAL, HIGH, NORMAL, LOW
    priority_score = db.Column(db.Float, default=0.0)
    priority_reason = db.Column(db.Text)
    status = db.Column(db.String(50), default="CREATED")
    # CREATED, PRIORITIZED, ALLOCATED, PICKING, PACKING,
    # QUALITY_CHECK, READY_TO_DISPATCH, DISPATCHED, COMPLETED, EXCEPTION
    deadline = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")
    allocations = db.relationship("Allocation", backref="order", lazy=True)
    pick_tasks = db.relationship("PickTask", backref="order", lazy=True)
    pack_tasks = db.relationship("PackTask", backref="order", lazy=True)
    quality_checks = db.relationship("QualityCheck", backref="order", lazy=True)
    exceptions = db.relationship("WarehouseException", backref="order", lazy=True)
    dispatch = db.relationship("Dispatch", backref="order", uselist=False, lazy=True)

    @property
    def total_value(self):
        return sum(
            (item.quantity * item.product.price)
            for item in self.items
            if item.product
        )

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "customer_type": self.customer_type,
            "priority": self.priority,
            "priority_score": self.priority_score,
            "priority_reason": self.priority_reason,
            "status": self.status,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "notes": self.notes,
            "total_value": self.total_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "item_count": len(self.items),
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    allocated_quantity = db.Column(db.Integer, default=0)
    picked_quantity = db.Column(db.Integer, default=0)
    packed_quantity = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "allocated_quantity": self.allocated_quantity,
            "picked_quantity": self.picked_quantity,
            "packed_quantity": self.packed_quantity,
        }


class Allocation(db.Model):
    __tablename__ = "allocations"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False)
    requested_quantity = db.Column(db.Integer, nullable=False)
    allocated_quantity = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(
        db.String(50), default="PENDING"
    )  # PENDING, ALLOCATED, PARTIAL, FAILED
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "inventory_id": self.inventory_id,
            "requested_quantity": self.requested_quantity,
            "allocated_quantity": self.allocated_quantity,
            "status": self.status,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PickTask(db.Model):
    __tablename__ = "pick_tasks"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    worker_name = db.Column(db.String(100))
    zone = db.Column(db.String(10))
    bin_location = db.Column(db.String(20))
    quantity = db.Column(db.Integer, nullable=False)
    sequence = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    product = db.relationship("Product", backref="pick_tasks", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "worker_name": self.worker_name,
            "zone": self.zone,
            "bin_location": self.bin_location,
            "quantity": self.quantity,
            "sequence": self.sequence,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class PackTask(db.Model):
    __tablename__ = "pack_tasks"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    packing_station = db.Column(db.String(50))
    worker_name = db.Column(db.String(100))
    status = db.Column(db.String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "packing_station": self.packing_station,
            "worker_name": self.worker_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class QualityCheck(db.Model):
    __tablename__ = "quality_checks"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    checked_by = db.Column(db.String(100))
    status = db.Column(db.String(50), default="PENDING")  # PENDING, PASSED, FAILED
    damaged_items = db.Column(db.Integer, default=0)
    missing_items = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    checked_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "checked_by": self.checked_by,
            "status": self.status,
            "damaged_items": self.damaged_items,
            "missing_items": self.missing_items,
            "notes": self.notes,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }


class WarehouseException(db.Model):
    __tablename__ = "warehouse_exceptions"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    exception_type = db.Column(db.String(50), nullable=False)
    # LOW_STOCK, OUT_OF_STOCK, DAMAGED_ITEM, MISSING_ITEM,
    # PICKING_DELAY, PACKING_DELAY, QUALITY_FAILURE, ALLOCATION_CONFLICT
    severity = db.Column(db.String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    description = db.Column(db.Text, nullable=False)
    recommended_action = db.Column(db.Text)
    status = db.Column(
        db.String(50), default="OPEN"
    )  # OPEN, IN_PROGRESS, RESOLVED, DISMISSED
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "order_number": self.order.order_number if self.order else None,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "product_sku": self.product.sku if self.product else None,
            "product_image_url": self.product.image_url if self.product else None,
            "exception_type": self.exception_type,
            "severity": self.severity,
            "description": self.description,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class Dispatch(db.Model):
    __tablename__ = "dispatches"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, unique=True
    )
    carrier = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    status = db.Column(
        db.String(50), default="PENDING"
    )  # PENDING, DISPATCHED, IN_TRANSIT, DELIVERED
    dispatch_time = db.Column(db.DateTime)
    estimated_delivery = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "carrier": self.carrier,
            "tracking_number": self.tracking_number,
            "status": self.status,
            "dispatch_time": (
                self.dispatch_time.isoformat() if self.dispatch_time else None
            ),
            "estimated_delivery": (
                self.estimated_delivery.isoformat()
                if self.estimated_delivery
                else None
            ),
        }


class InventoryMovement(db.Model):
    __tablename__ = "inventory_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    inventory_id = db.Column(
        db.Integer, db.ForeignKey("inventory.id"), nullable=False
    )
    movement_type = db.Column(
        db.String(50), nullable=False
    )  # INBOUND, OUTBOUND, ALLOCATION, RELEASE, ADJUSTMENT, DAMAGE
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "inventory_id": self.inventory_id,
            "movement_type": self.movement_type,
            "quantity": self.quantity,
            "reference": self.reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), default="Warehouse Manager")
    auth_provider = db.Column(db.String(50), default="EMAIL_OTP")  # EMAIL_OTP, GOOGLE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "auth_provider": self.auth_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

