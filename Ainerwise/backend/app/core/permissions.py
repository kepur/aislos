import enum


class UserRole(str, enum.Enum):
    # internal staff (frontend-admin)
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SALES_MANAGER = "sales_manager"
    PROJECT_MANAGER = "project_manager"
    FINANCE = "finance"
    # customers (frontend-h5; UI shows "Customer", backend keeps `buyer` = owner)
    BUYER = "buyer"
    CUSTOMER_USER = "customer_user"
    # supply / delivery network (frontend-h5 partner layout)
    VENDOR = "vendor"
    DEVELOPER = "developer"
    SERVICE_PARTNER = "service_partner"  # = partner owner
    PARTNER_WORKER = "partner_worker"
    MAINTENANCE_WORKER = "maintenance_worker"


# Sensitive operations (settings, finance writes, awards) stay with these two
# until real staff exist — granular staff permissions come with real hires.
ADMIN_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN}
STAFF_ROLES = ADMIN_ROLES | {UserRole.SALES_MANAGER, UserRole.PROJECT_MANAGER, UserRole.FINANCE}
PARTNER_ROLES = {UserRole.SERVICE_PARTNER, UserRole.PARTNER_WORKER, UserRole.MAINTENANCE_WORKER}
CUSTOMER_ROLES = {UserRole.BUYER, UserRole.CUSTOMER_USER}
ALL_ROLES = set(UserRole)
