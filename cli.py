"""CLI for manually testing the veryon_wc library."""

import argparse
import json
import os
import sys
from pathlib import Path

from veryon_wc import WcClient


def _load_dotenv(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file, without overriding existing vars."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).resolve().parent / ".env")


def _client() -> WcClient:
    base_url = os.environ.get("WC_BASE_URL", "https://ia.ebis5.com/api/integration/external")
    username = os.environ.get("WC_USERNAME")
    password = os.environ.get("WC_PASSWORD")
    if not username or not password:
        print("error: set WC_USERNAME and WC_PASSWORD (or create a .env file)", file=sys.stderr)
        sys.exit(1)
    return WcClient(base_url, username, password)


def _out(data):
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# workorders
# ---------------------------------------------------------------------------

def _wo_lists(args):
    _out(_client().get_workorder_lists(args.name))


def _wo_listing_lists(args):
    _out(_client().get_workorder_listing_lists(args.name or None))


def _wo_export(args):
    _out(_client().export_workorders(
        city_ids=args.city or None,
        created_dates=args.created or None,
        completed_dates=args.completed or None,
        include_parts=args.parts,
        include_service=args.service,
        include_invoice_totals=args.invoice_totals,
    ))


def _wo_totals(args):
    _out(_client().get_workorder_totals(
        ac_reg_num=args.reg_num,
        created_dates=args.created or None,
        completed_dates=args.completed or None,
        include_open_wos=args.open,
    ))


def _wo_listing(args):
    _out(_client().get_workorder_listing(
        wo_status_id=int(args.status),
        wo_type_id=int(args.type),
        city_ids=args.city or None,
    ))


def _wo_create(args):
    items = None
    if args.discrepancy:
        items = [{"LineNumber": i + 1, "Discrepancy": d} for i, d in enumerate(args.discrepancy)]
    _out(_client().create_update_workorder(reg_num=args.reg_num, items=items))


# ---------------------------------------------------------------------------
# equipment
# ---------------------------------------------------------------------------

def _eq_lists(args):
    _out(_client().get_equipment_listing_lists(args.name or None))


def _eq_listing(args):
    _out(_client().get_equipment_listing(
        city_ids=args.city or None,
        vin=args.vin,
        serial_no=args.serial,
        inactive_include=args.inactive,
    ))


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

def _users_lists(args):
    _out(_client().get_user_lists(args.name or None))


def _users_listing(args):
    _out(_client().get_users(show_inactive=args.inactive))


# ---------------------------------------------------------------------------
# parser setup
# ---------------------------------------------------------------------------

def _add_wo_parsers(parent):
    wo = parent.add_parser("workorders", aliases=["wo"], help="work order commands")
    sub = wo.add_subparsers(dest="action", required=True)

    p = sub.add_parser("lists", help="fetch reference lists")
    p.add_argument("--name", metavar="LIST_NAME", help="specific list to fetch, e.g. CityID")
    p.set_defaults(func=_wo_lists)

    p = sub.add_parser("listing-lists", help="fetch listing reference lists (WoStatusID, WoTypeID, etc.)")
    p.add_argument("--name", nargs="+", metavar="LIST_NAME", help="specific list(s) to fetch")
    p.set_defaults(func=_wo_listing_lists)

    p = sub.add_parser("export", help="export work orders")
    p.add_argument("--city", nargs="+", metavar="ID")
    p.add_argument("--created", nargs="+", metavar="YYYY-MM-DD")
    p.add_argument("--completed", nargs="+", metavar="YYYY-MM-DD")
    p.add_argument("--parts", action="store_true")
    p.add_argument("--service", action="store_true")
    p.add_argument("--invoice-totals", action="store_true")
    p.set_defaults(func=_wo_export)

    p = sub.add_parser("totals", help="get work order totals")
    p.add_argument("--reg-num", metavar="TAIL", help="aircraft tail number")
    p.add_argument("--created", nargs="+", metavar="YYYY-MM-DD")
    p.add_argument("--completed", nargs="+", metavar="YYYY-MM-DD")
    p.add_argument("--open", action="store_true", help="include open work orders")
    p.set_defaults(func=_wo_totals)

    p = sub.add_parser("listing", help="get work order listing")
    p.add_argument("--status", required=True, metavar="STATUS_ID", help="e.g. 'Open' or 101")
    p.add_argument("--type", required=True, metavar="TYPE_ID", help="e.g. 'Scheduled' or 101")
    p.add_argument("--city", nargs="+", metavar="ID")
    p.set_defaults(func=_wo_listing)

    p = sub.add_parser("create", help="create a work order")
    p.add_argument("--reg-num", required=True, metavar="TAIL", help="aircraft tail number")
    p.add_argument("--discrepancy", nargs="+", metavar="TEXT", help="one discrepancy per item")
    p.set_defaults(func=_wo_create)


def _add_eq_parsers(parent):
    eq = parent.add_parser("equipment", aliases=["eq"], help="equipment commands")
    sub = eq.add_subparsers(dest="action", required=True)

    p = sub.add_parser("lists", help="fetch reference lists")
    p.add_argument("--name", nargs="+", metavar="LIST_NAME")
    p.set_defaults(func=_eq_lists)

    p = sub.add_parser("listing", help="list equipment")
    p.add_argument("--city", nargs="+", metavar="ID")
    p.add_argument("--vin", metavar="VIN")
    p.add_argument("--serial", metavar="SERIAL_NO")
    p.add_argument("--inactive", action="store_true", help="include inactive equipment")
    p.set_defaults(func=_eq_listing)


def _add_user_parsers(parent):
    u = parent.add_parser("users", help="user commands")
    sub = u.add_subparsers(dest="action", required=True)

    p = sub.add_parser("lists", help="fetch reference lists")
    p.add_argument("--name", nargs="+", metavar="LIST_NAME")
    p.set_defaults(func=_users_lists)

    p = sub.add_parser("listing", help="list users")
    p.add_argument("--inactive", action="store_true", help="include inactive users")
    p.set_defaults(func=_users_listing)


def main():
    parser = argparse.ArgumentParser(
        prog="veryonwc",
        description="Veryon Workcenter (WC) CLI — test the veryon_wc library against a live API",
    )
    parser.add_argument(
        "--url",
        metavar="URL",
        help="override WC_BASE_URL",
        default=None,
    )
    sub = parser.add_subparsers(dest="resource", required=True)

    _add_wo_parsers(sub)
    _add_eq_parsers(sub)
    _add_user_parsers(sub)

    args = parser.parse_args()

    if args.url:
        os.environ["WC_BASE_URL"] = args.url

    args.func(args)


if __name__ == "__main__":
    main()
