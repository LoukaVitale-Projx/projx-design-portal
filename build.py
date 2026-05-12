#!/usr/bin/env python3
"""
ProjX House & Land Design Portal — V1 Prototype
Fetches live Oakland Estate lot data from Monday.com and generates index.html
"""

import json, os, sys, urllib.request, datetime

BOARD_ID = "5024497655"
API_URL = "https://api.monday.com/v2"


def get_token():
    env_path = os.path.expanduser("~/.openclaw/workspace/.env")
    with open(env_path) as f:
        for line in f:
            if line.startswith("MONDAY_API_TOKEN="):
                return line.strip().split("=", 1)[1].strip()
    raise RuntimeError("MONDAY_API_TOKEN not found in .env")


def monday_query(query, token):
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json", "Authorization": token},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_oakland_lots(token):
    q = """
    {
      boards(ids: [5024497655]) {
        items_page(limit: 200) {
          items {
            id name group { title }
            column_values(ids: [
              "color_mkwzqgxz",
              "numeric_mkwtm36",
              "numeric_mkwtgeke",
              "dropdown_mkwtezxj",
              "dropdown_mkwttxbv"
            ]) { id text }
          }
        }
      }
    }
    """
    COL_MAP = {
        "color_mkwzqgxz": "availability",
        "numeric_mkwtm36": "lot_price",
        "numeric_mkwtgeke": "lot_size",
        "dropdown_mkwtezxj": "type",
        "dropdown_mkwttxbv": "stage",
    }

    data = monday_query(q, token)
    raw_items = data["data"]["boards"][0]["items_page"]["items"]

    lots = []
    for item in raw_items:
        row = {"id": item["id"], "name": item["name"], "group": item["group"]["title"]}
        for cv in item["column_values"]:
            key = COL_MAP.get(cv["id"], cv["id"])
            row[key] = cv["text"] or ""

        avail = row.get("availability", "")
        if avail in ("Available", "Reserved", "Unreleased", ""):
            lot_size = 0
            try:
                lot_size = float(str(row.get("lot_size", "0")).replace(",", ""))
            except Exception:
                pass

            price = 0
            try:
                price = float(str(row.get("lot_price", "0")).replace(",", ""))
            except Exception:
                pass

            # Estimate frontage: typical SEQ subdivision ~28m depth
            if lot_size > 0:
                frontage = round(lot_size / 28)
            else:
                frontage = 12
            frontage = max(10, min(frontage, 25))

            lots.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "availability": avail if avail else "Available",
                    "price": int(price),
                    "lot_size": int(lot_size),
                    "frontage": frontage,
                    "type": row.get("type", "H&L"),
                    "stage": row.get("stage", "Stage 1"),
                    "project": "oakland",
                }
            )

    lots.sort(key=lambda x: x["name"])
    return lots


# ── Static sample data for Woodchester & Ooranya ─────────────────────────────

WOODCHESTER_LOTS = [
    {"id": "wc1","name": "Lot 1","availability": "Available","price": 245000,"lot_size": 4000,"frontage": 40,"type": "Rural Residential","stage": "Stage 1","project": "woodchester"},
    {"id": "wc2","name": "Lot 2","availability": "Available","price": 235000,"lot_size": 3500,"frontage": 35,"type": "Rural Residential","stage": "Stage 1","project": "woodchester"},
    {"id": "wc3","name": "Lot 3","availability": "Available","price": 275000,"lot_size": 5200,"frontage": 45,"type": "Rural Residential","stage": "Stage 1","project": "woodchester"},
    {"id": "wc4","name": "Lot 4","availability": "Reserved","price": 265000,"lot_size": 4800,"frontage": 42,"type": "Rural Residential","stage": "Stage 1","project": "woodchester"},
    {"id": "wc5","name": "Lot 5","availability": "Available","price": 295000,"lot_size": 6100,"frontage": 50,"type": "Rural Residential","stage": "Stage 2","project": "woodchester"},
    {"id": "wc6","name": "Lot 6","availability": "Available","price": 228000,"lot_size": 3200,"frontage": 30,"type": "Rural Residential","stage": "Stage 1","project": "woodchester"},
]

OORANYA_LOTS = [
    {"id": "oo1","name": "Lot 101","availability": "Available","price": 395000,"lot_size": 450,"frontage": 16,"type": "H&L","stage": "Stage 1","project": "ooranya"},
    {"id": "oo2","name": "Lot 102","availability": "Available","price": 425000,"lot_size": 512,"frontage": 18,"type": "H&L","stage": "Stage 1","project": "ooranya"},
    {"id": "oo3","name": "Lot 103","availability": "Available","price": 375000,"lot_size": 380,"frontage": 14,"type": "H&L","stage": "Stage 1","project": "ooranya"},
    {"id": "oo4","name": "Lot 104","availability": "Reserved","price": 455000,"lot_size": 625,"frontage": 20,"type": "H&L","stage": "Stage 2","project": "ooranya"},
    {"id": "oo5","name": "Lot 105","availability": "Available","price": 405000,"lot_size": 440,"frontage": 16,"type": "H&L","stage": "Stage 1","project": "ooranya"},
    {"id": "oo6","name": "Lot 106","availability": "Available","price": 440000,"lot_size": 580,"frontage": 20,"type": "H&L","stage": "Stage 2","project": "ooranya"},
]


# ── HTML generation ────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ProjX | House & Land Design Portal</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
/* ── Reset & Variables ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#001E2E;
  --navy-mid:#002D44;
  --navy-light:#003855;
  --silver:#CBD2D8;
  --silver-light:#E8EBED;
  --silver-xlight:#F4F5F7;
  --accent:#00A3E0;
  --accent-dark:#0082B3;
  --accent-glow:rgba(0,163,224,0.15);
  --green:#10B981;
  --amber:#F59E0B;
  --red:#EF4444;
  --white:#FFFFFF;
  --bg:#F0F2F5;
  --text:#001E2E;
  --text-mid:#374151;
  --text-light:#6B7280;
  --text-xlight:#9CA3AF;
  --shadow-sm:0 1px 3px rgba(0,30,46,0.08),0 2px 6px rgba(0,30,46,0.04);
  --shadow-md:0 4px 12px rgba(0,30,46,0.1),0 2px 4px rgba(0,30,46,0.06);
  --shadow-lg:0 8px 24px rgba(0,30,46,0.12),0 4px 8px rgba(0,30,46,0.08);
  --shadow-xl:0 16px 48px rgba(0,30,46,0.16),0 8px 16px rgba(0,30,46,0.08);
  --radius:12px;
  --radius-sm:8px;
  --radius-lg:16px;
  --radius-xl:24px;
  --transition:0.2s ease;
}
body{font-family:'Montserrat',sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh;-webkit-font-smoothing:antialiased}
img{display:block;max-width:100%}
button{cursor:pointer;font-family:'Montserrat',sans-serif}
input,select,textarea{font-family:'Montserrat',sans-serif}

/* ── Password Gate ── */
#auth-gate{
  position:fixed;inset:0;z-index:9999;
  background:var(--navy);
  display:flex;align-items:center;justify-content:center;flex-direction:column;
}
#auth-gate.hidden{display:none}
.gate-wrap{text-align:center;max-width:420px;width:90%;padding:0 16px}
.gate-logo{
  width:56px;height:56px;background:var(--accent);border-radius:16px;
  display:flex;align-items:center;justify-content:center;margin:0 auto 24px;
  font-size:22px;font-weight:900;color:#fff;letter-spacing:-1px;
}
.gate-box{
  background:#fff;border-radius:var(--radius-xl);padding:40px 36px;
  box-shadow:var(--shadow-xl);
}
.gate-box h2{font-size:20px;font-weight:800;color:var(--navy);margin-bottom:4px}
.gate-box .gate-sub{font-size:13px;color:var(--text-light);margin-bottom:28px}
.gate-badge{
  display:inline-flex;align-items:center;gap:6px;
  background:#FEF3C7;color:#92400E;font-size:10px;font-weight:700;
  padding:4px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:0.5px;
  margin-bottom:20px;
}
.gate-input{
  width:100%;padding:14px 18px;border:2px solid var(--silver-light);border-radius:var(--radius-sm);
  font-size:16px;font-family:'Montserrat',sans-serif;text-align:center;
  letter-spacing:4px;outline:none;transition:border-color var(--transition);color:var(--navy);
  background:#fff;
}
.gate-input:focus{border-color:var(--accent)}
.gate-input.error{border-color:var(--red);animation:shake 0.4s}
.gate-btn{
  margin-top:14px;width:100%;padding:15px;
  background:var(--navy);color:#fff;border:none;border-radius:var(--radius-sm);
  font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  transition:background var(--transition),transform var(--transition);
}
.gate-btn:hover{background:var(--navy-mid);transform:translateY(-1px)}
.gate-btn:active{transform:translateY(0)}
.gate-footer{color:rgba(203,210,216,0.5);font-size:11px;margin-top:20px;letter-spacing:0.5px}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-8px)}75%{transform:translateX(8px)}}

/* ── App Shell ── */
#app{display:none;min-height:100vh;flex-direction:column}
#app.visible{display:flex}

/* ── Top Bar ── */
.top-bar{
  background:var(--navy);padding:0 32px;height:64px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
  box-shadow:0 2px 16px rgba(0,0,0,0.2);
}
.top-bar-left{display:flex;align-items:center;gap:16px}
.top-logo{
  background:var(--accent);color:#fff;font-size:13px;font-weight:900;
  padding:6px 12px;border-radius:8px;letter-spacing:-0.3px;
}
.top-title{color:#fff;font-size:15px;font-weight:700;letter-spacing:-0.3px}
.top-title span{color:var(--silver);font-weight:400;font-size:13px}
.top-bar-right{display:flex;align-items:center;gap:12px}
.confidential-badge{
  background:rgba(245,158,11,0.15);color:#F59E0B;border:1px solid rgba(245,158,11,0.3);
  font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px;
  text-transform:uppercase;letter-spacing:0.5px;
}
.top-step-label{color:var(--silver);font-size:12px;font-weight:500}

/* ── Progress Bar ── */
.progress-bar-wrap{background:#fff;border-bottom:1px solid var(--silver-light);padding:0 32px}
.progress-steps{
  display:flex;align-items:stretch;max-width:1100px;margin:0 auto;
  overflow-x:auto;scrollbar-width:none;
}
.progress-steps::-webkit-scrollbar{display:none}
.prog-step{
  flex:1;min-width:120px;padding:14px 16px;
  display:flex;align-items:center;gap:10px;
  border-bottom:3px solid transparent;
  transition:all var(--transition);cursor:default;white-space:nowrap;
}
.prog-step.done{border-bottom-color:var(--accent)}
.prog-step.active{border-bottom-color:var(--navy)}
.prog-step-num{
  width:26px;height:26px;border-radius:50%;background:var(--silver-light);
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:var(--text-light);flex-shrink:0;
  transition:all var(--transition);
}
.prog-step.done .prog-step-num{background:var(--accent);color:#fff}
.prog-step.active .prog-step-num{background:var(--navy);color:#fff}
.prog-step-label{font-size:11px;font-weight:600;color:var(--text-light);transition:color var(--transition)}
.prog-step.done .prog-step-label{color:var(--accent)}
.prog-step.active .prog-step-label{color:var(--navy);font-weight:700}

/* ── Main Content ── */
.main-content{flex:1;padding:32px;max-width:1200px;margin:0 auto;width:100%}
.step-pane{display:none;animation:fadeIn 0.3s ease}
.step-pane.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

/* ── Step Headers ── */
.step-header{margin-bottom:28px}
.step-header h2{font-size:26px;font-weight:800;color:var(--navy);letter-spacing:-0.5px;margin-bottom:6px}
.step-header p{font-size:14px;color:var(--text-light);max-width:600px}

/* ── Nav Footer ── */
.nav-footer{
  background:#fff;border-top:1px solid var(--silver-light);
  padding:20px 32px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;bottom:0;z-index:50;
}
.nav-left{display:flex;align-items:center;gap:12px}
.nav-right{display:flex;align-items:center;gap:12px}
.btn-back{
  background:#fff;border:2px solid var(--silver-light);color:var(--text-mid);
  padding:12px 24px;border-radius:var(--radius-sm);font-size:13px;font-weight:700;
  letter-spacing:0.5px;transition:all var(--transition);
}
.btn-back:hover{border-color:var(--navy);color:var(--navy)}
.btn-next{
  background:var(--navy);color:#fff;border:none;
  padding:12px 32px;border-radius:var(--radius-sm);font-size:13px;font-weight:700;
  letter-spacing:0.5px;transition:all var(--transition);
  display:flex;align-items:center;gap:8px;
}
.btn-next:hover{background:var(--accent)}
.btn-next:disabled{background:var(--silver-light);color:var(--text-xlight);cursor:not-allowed}
.btn-next svg{transition:transform var(--transition)}
.btn-next:hover:not(:disabled) svg{transform:translateX(4px)}
.nav-info{font-size:12px;color:var(--text-xlight)}

/* ── Step 1: Project Cards ── */
.project-grid{
  display:grid;grid-template-columns:repeat(3,1fr);gap:20px;
}
.project-card{
  background:#fff;border-radius:var(--radius-lg);overflow:hidden;
  box-shadow:var(--shadow-sm);border:2px solid transparent;
  transition:all 0.25s ease;cursor:pointer;
}
.project-card:hover{box-shadow:var(--shadow-lg);transform:translateY(-4px)}
.project-card.selected{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-glow),var(--shadow-md)}
.project-hero{
  height:200px;background:linear-gradient(135deg,var(--navy) 0%,var(--navy-light) 50%,#004a70 100%);
  position:relative;overflow:hidden;
  display:flex;align-items:flex-end;padding:20px;
}
.project-hero::before{
  content:'';position:absolute;inset:0;
  background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
.project-hero-icon{
  width:48px;height:48px;background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
  border-radius:12px;display:flex;align-items:center;justify-content:center;
  font-size:22px;position:absolute;top:16px;right:16px;
}
.project-status-chip{
  background:var(--accent);color:#fff;font-size:10px;font-weight:700;
  padding:4px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:0.5px;
  position:absolute;top:16px;left:16px;
}
.project-hero-text{color:#fff;position:relative}
.project-hero-text .suburb{font-size:12px;color:rgba(255,255,255,0.6);margin-bottom:2px}
.project-hero-text .name{font-size:18px;font-weight:800;letter-spacing:-0.3px}
.project-body{padding:20px}
.project-stats{display:flex;gap:16px;margin-bottom:14px}
.project-stat{flex:1;text-align:center;padding:10px;background:var(--silver-xlight);border-radius:var(--radius-sm)}
.project-stat .val{font-size:16px;font-weight:800;color:var(--navy)}
.project-stat .lbl{font-size:10px;font-weight:600;color:var(--text-xlight);text-transform:uppercase;letter-spacing:0.3px;margin-top:2px}
.project-price{font-size:13px;color:var(--text-light);margin-bottom:14px}
.project-price strong{color:var(--navy);font-weight:700}
.project-features{display:flex;flex-wrap:wrap;gap:6px}
.project-feature{
  background:var(--accent-glow);color:var(--accent-dark);
  font-size:10px;font-weight:600;padding:3px 8px;border-radius:20px;
}
.project-select-btn{
  width:100%;margin-top:14px;padding:10px;background:var(--navy);color:#fff;
  border:none;border-radius:var(--radius-sm);font-size:12px;font-weight:700;
  letter-spacing:0.5px;text-transform:uppercase;transition:background var(--transition);
}
.project-card.selected .project-select-btn{background:var(--accent)}
.project-select-btn:hover{background:var(--accent)}

/* ── Step 2: Lot Selection ── */
.lot-controls{
  display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;align-items:center;
}
.lot-controls select,.lot-controls input[type=range]{
  padding:10px 14px;border:2px solid var(--silver-light);border-radius:var(--radius-sm);
  font-size:12px;font-weight:600;color:var(--navy);outline:none;
  transition:border-color var(--transition);background:#fff;
}
.lot-controls select:focus{border-color:var(--accent)}
.lot-controls .filter-label{font-size:11px;font-weight:600;color:var(--text-light);text-transform:uppercase;letter-spacing:0.5px}
.lot-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.lot-card{
  background:#fff;border-radius:var(--radius);padding:20px;
  box-shadow:var(--shadow-sm);border:2px solid transparent;
  transition:all 0.2s ease;cursor:pointer;
}
.lot-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px)}
.lot-card.selected{border-color:var(--accent);background:linear-gradient(135deg,#fff 0%,#f0f9ff 100%)}
.lot-card-head{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px}
.lot-name{font-size:18px;font-weight:800;color:var(--navy)}
.lot-stage{font-size:10px;font-weight:600;color:var(--text-xlight);margin-top:2px}
.lot-avail{padding:4px 10px;border-radius:20px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.3px}
.lot-avail.Available{background:#D1FAE5;color:#065F46}
.lot-avail.Reserved{background:#E0E7FF;color:#3730A3}
.lot-avail.Unreleased{background:#F3F4F6;color:#6B7280}
.lot-specs{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px}
.lot-spec{padding:8px 10px;background:var(--silver-xlight);border-radius:var(--radius-sm);text-align:center}
.lot-spec .sv{font-size:16px;font-weight:800;color:var(--navy)}
.lot-spec .sl{font-size:9px;font-weight:600;color:var(--text-xlight);text-transform:uppercase;letter-spacing:0.3px}
.lot-price-row{display:flex;align-items:center;justify-content:space-between}
.lot-price{font-size:20px;font-weight:800;color:var(--accent)}
.lot-select-btn{
  background:var(--navy);color:#fff;border:none;
  padding:8px 16px;border-radius:var(--radius-sm);font-size:11px;font-weight:700;
  letter-spacing:0.3px;text-transform:uppercase;transition:background var(--transition);
}
.lot-card.selected .lot-select-btn{background:var(--accent)}
.lot-select-btn:hover{background:var(--accent)}
.no-lots{
  grid-column:1/-1;text-align:center;padding:60px 20px;
  color:var(--text-xlight);font-size:14px;
}

/* ── Step 3: Builder Selection ── */
.builder-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}
.builder-card{
  background:#fff;border-radius:var(--radius-lg);padding:24px;
  box-shadow:var(--shadow-sm);border:2px solid transparent;
  transition:all 0.2s ease;cursor:pointer;position:relative;
}
.builder-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px)}
.builder-card.selected{border-color:var(--accent);background:linear-gradient(135deg,#fff 0%,#f0f9ff 100%)}
.builder-card.disabled{opacity:0.5;cursor:not-allowed;pointer-events:none}
.builder-card.disabled:hover{box-shadow:var(--shadow-sm);transform:none}
.builder-check{
  position:absolute;top:16px;right:16px;width:28px;height:28px;
  border:2px solid var(--silver);border-radius:50%;background:#fff;
  display:flex;align-items:center;justify-content:center;transition:all var(--transition);
}
.builder-card.selected .builder-check{background:var(--accent);border-color:var(--accent)}
.builder-logo-area{
  width:56px;height:56px;border-radius:14px;margin-bottom:16px;
  display:flex;align-items:center;justify-content:center;
  font-size:22px;font-weight:900;color:#fff;
}
.builder-name{font-size:17px;font-weight:800;color:var(--navy);margin-bottom:4px}
.builder-tagline{font-size:12px;color:var(--text-light);margin-bottom:16px}
.builder-attrs{display:flex;flex-direction:column;gap:8px}
.builder-attr{display:flex;align-items:center;gap:10px;font-size:12px}
.builder-attr-icon{width:28px;height:28px;background:var(--silver-xlight);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.builder-attr-label{color:var(--text-light)}
.builder-attr-val{font-weight:700;color:var(--navy);margin-left:auto}
.builder-tier{
  display:inline-block;margin-top:14px;
  padding:4px 10px;border-radius:20px;font-size:10px;font-weight:700;
  text-transform:uppercase;letter-spacing:0.5px;
}
.tier-entry{background:#F0FDF4;color:#166534}
.tier-entry-mid{background:#EFF6FF;color:#1E40AF}
.tier-mid{background:#EEF2FF;color:#3730A3}
.tier-mid-premium{background:#FDF4FF;color:#6B21A8}
.tier-premium{background:#FFF7ED;color:#9A3412}
.builder-hint{
  text-align:center;margin-bottom:16px;padding:12px 16px;
  background:var(--silver-xlight);border-radius:var(--radius-sm);
  font-size:12px;color:var(--text-mid);
}
.builder-hint strong{color:var(--navy)}

/* ── Step 4: Design Browsing ── */
.design-filter-bar{
  background:#fff;border-radius:var(--radius);padding:16px 20px;
  box-shadow:var(--shadow-sm);margin-bottom:20px;
  display:flex;align-items:center;gap:12px;flex-wrap:wrap;
}
.filter-chip{
  padding:6px 14px;border-radius:20px;border:2px solid var(--silver-light);
  font-size:11px;font-weight:600;color:var(--text-mid);cursor:pointer;
  transition:all var(--transition);background:#fff;
}
.filter-chip.active{border-color:var(--navy);background:var(--navy);color:#fff}
.filter-chip:hover:not(.active){border-color:var(--accent);color:var(--accent)}
.design-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}
.design-card{
  background:#fff;border-radius:var(--radius-lg);overflow:hidden;
  box-shadow:var(--shadow-sm);border:2px solid transparent;
  transition:all 0.2s ease;cursor:pointer;
}
.design-card:hover{box-shadow:var(--shadow-lg);transform:translateY(-3px)}
.design-card.selected{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-glow),var(--shadow-md)}
.design-card.incompatible{opacity:0.5}
.design-thumb{
  height:180px;position:relative;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
.design-thumb-bg{
  position:absolute;inset:0;
  background:linear-gradient(135deg,#1a2f3f 0%,#2a4a5e 40%,#1a3340 100%);
}
.design-thumb-house{
  position:relative;z-index:1;
  font-size:64px;opacity:0.15;
}
.design-thumb-overlay{
  position:absolute;inset:0;z-index:2;
  display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-end;
  padding:16px;
  background:linear-gradient(to top,rgba(0,30,46,0.8) 0%,transparent 60%);
}
.design-thumb-name{color:#fff;font-size:16px;font-weight:800;letter-spacing:-0.3px}
.design-thumb-builder{color:rgba(255,255,255,0.6);font-size:11px;font-weight:500;margin-top:2px}
.design-compat-badge{
  position:absolute;top:12px;right:12px;z-index:3;
  padding:4px 10px;border-radius:20px;font-size:10px;font-weight:700;
  text-transform:uppercase;letter-spacing:0.3px;
}
.design-compat-badge.fit{background:var(--green);color:#fff}
.design-compat-badge.tight{background:var(--amber);color:#fff}
.design-compat-badge.no{background:var(--red);color:#fff}
.design-body{padding:18px}
.design-specs{display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.design-spec-pill{
  display:flex;align-items:center;gap:4px;
  background:var(--silver-xlight);padding:4px 9px;border-radius:20px;
  font-size:11px;font-weight:600;color:var(--text-mid);
}
.design-footer{display:flex;align-items:center;justify-content:space-between}
.design-size{font-size:12px;color:var(--text-light)}
.design-price{font-size:16px;font-weight:800;color:var(--accent)}
.design-frontage-req{font-size:10px;color:var(--text-xlight);margin-top:4px}
.design-shortlist-btn{
  margin-top:12px;width:100%;padding:9px;
  background:var(--navy);color:#fff;border:none;
  border-radius:var(--radius-sm);font-size:11px;font-weight:700;
  letter-spacing:0.3px;text-transform:uppercase;transition:background var(--transition);
}
.design-card.selected .design-shortlist-btn{background:var(--accent)}
.design-shortlist-btn:hover{background:var(--accent)}
.frontage-notice{
  padding:12px 16px;background:#FEF3C7;border-radius:var(--radius-sm);
  border-left:4px solid var(--amber);font-size:12px;color:#92400E;
  margin-bottom:16px;
}
.frontage-notice strong{font-weight:700}

/* ── Step 5: Customize ── */
.customize-layout{display:grid;grid-template-columns:1fr 360px;gap:24px;align-items:start}
.customize-main{}
.customize-section{
  background:#fff;border-radius:var(--radius-lg);padding:24px;
  box-shadow:var(--shadow-sm);margin-bottom:20px;
}
.customize-section-title{
  font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
  color:var(--navy);margin-bottom:18px;padding-bottom:10px;
  border-bottom:2px solid var(--silver-xlight);
}
.facade-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.facade-option{
  border:2px solid var(--silver-light);border-radius:var(--radius);
  padding:16px;cursor:pointer;transition:all var(--transition);
}
.facade-option:hover{border-color:var(--accent)}
.facade-option.selected{border-color:var(--accent);background:var(--accent-glow)}
.facade-thumb{
  height:80px;border-radius:var(--radius-sm);margin-bottom:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:28px;position:relative;overflow:hidden;
}
.facade-thumb-bg{position:absolute;inset:0}
.facade-thumb-icon{position:relative;z-index:1;font-size:28px;opacity:0.5}
.facade-name{font-size:13px;font-weight:700;color:var(--navy)}
.facade-price{font-size:12px;color:var(--text-light);margin-top:2px}
.inclusions-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.incl-option{
  border:2px solid var(--silver-light);border-radius:var(--radius);
  padding:18px 14px;cursor:pointer;transition:all var(--transition);text-align:center;
}
.incl-option:hover{border-color:var(--accent)}
.incl-option.selected{border-color:var(--navy);background:var(--navy)}
.incl-option.selected .incl-name{color:#fff}
.incl-option.selected .incl-desc{color:rgba(255,255,255,0.7)}
.incl-option.selected .incl-price{color:var(--accent)}
.incl-name{font-size:15px;font-weight:800;color:var(--navy);margin-bottom:6px}
.incl-desc{font-size:11px;color:var(--text-light);margin-bottom:10px;line-height:1.4}
.incl-price{font-size:14px;font-weight:700;color:var(--accent)}
.upgrades-grid{display:flex;flex-direction:column;gap:10px}
.upgrade-item{
  display:flex;align-items:center;gap:14px;
  padding:14px 16px;border:2px solid var(--silver-light);border-radius:var(--radius);
  cursor:pointer;transition:all var(--transition);background:#fff;
}
.upgrade-item:hover{border-color:var(--accent)}
.upgrade-item.selected{border-color:var(--accent);background:var(--accent-glow)}
.upgrade-check{
  width:22px;height:22px;border:2px solid var(--silver);border-radius:6px;
  flex-shrink:0;display:flex;align-items:center;justify-content:center;
  transition:all var(--transition);
}
.upgrade-item.selected .upgrade-check{background:var(--accent);border-color:var(--accent)}
.upgrade-icon{font-size:20px;flex-shrink:0}
.upgrade-info{flex:1}
.upgrade-name{font-size:13px;font-weight:700;color:var(--navy)}
.upgrade-desc{font-size:11px;color:var(--text-light);margin-top:2px}
.upgrade-price{font-size:13px;font-weight:700;color:var(--accent);flex-shrink:0}

/* ── Pricing Sidebar ── */
.pricing-sidebar{
  background:var(--navy);border-radius:var(--radius-lg);padding:24px;
  color:#fff;position:sticky;top:88px;
}
.pricing-sidebar h3{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--silver);margin-bottom:20px}
.pricing-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.08)}
.pricing-row:last-of-type{border-bottom:none}
.pricing-row-label{font-size:12px;color:var(--silver)}
.pricing-row-val{font-size:13px;font-weight:700;color:#fff}
.pricing-total{
  margin-top:16px;padding:16px;background:rgba(0,163,224,0.15);
  border-radius:var(--radius);border:1px solid rgba(0,163,224,0.3);
  text-align:center;
}
.pricing-total .label{font-size:11px;font-weight:600;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px}
.pricing-total .amount{font-size:28px;font-weight:900;color:var(--accent);letter-spacing:-1px}
.pricing-total .qualifier{font-size:10px;color:rgba(255,255,255,0.4);margin-top:4px}
.pricing-breakdown{margin-top:12px}
.pricing-design-preview{
  padding:12px;background:rgba(255,255,255,0.05);border-radius:var(--radius-sm);
  margin-bottom:16px;
}
.pricing-design-name{font-size:13px;font-weight:700;color:#fff}
.pricing-design-sub{font-size:11px;color:var(--silver);margin-top:2px}

/* ── Step 6: Summary & EOI ── */
.summary-layout{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}
.summary-card{
  background:#fff;border-radius:var(--radius-lg);padding:24px;
  box-shadow:var(--shadow-sm);
}
.summary-card h3{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-light);margin-bottom:16px}
.summary-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--silver-xlight);font-size:13px}
.summary-row:last-child{border-bottom:none}
.summary-row .s-label{color:var(--text-light)}
.summary-row .s-val{font-weight:700;color:var(--navy)}
.summary-total-card{
  background:linear-gradient(135deg,var(--navy) 0%,var(--navy-light) 100%);
  border-radius:var(--radius-lg);padding:28px;color:#fff;
  box-shadow:var(--shadow-lg);margin-bottom:24px;
  display:flex;align-items:center;justify-content:space-between;
}
.summary-total-left .label{font-size:12px;font-weight:600;color:var(--silver);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px}
.summary-total-left .amount{font-size:36px;font-weight:900;color:#fff;letter-spacing:-1.5px}
.summary-total-left .qualifier{font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px}
.summary-total-right{text-align:right}
.summary-builders-chips{display:flex;gap:8px;flex-wrap:wrap}
.summary-builder-chip{
  background:rgba(0,163,224,0.15);color:var(--accent);border:1px solid rgba(0,163,224,0.3);
  padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;
}
.eoi-section{
  background:#fff;border-radius:var(--radius-lg);padding:28px;
  box-shadow:var(--shadow-sm);
}
.eoi-section h3{font-size:20px;font-weight:800;color:var(--navy);margin-bottom:6px}
.eoi-section p{font-size:13px;color:var(--text-light);margin-bottom:24px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.form-field{display:flex;flex-direction:column;gap:6px}
.form-field.full{grid-column:1/-1}
.form-field label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-mid)}
.form-field input,.form-field select,.form-field textarea{
  padding:12px 14px;border:2px solid var(--silver-light);border-radius:var(--radius-sm);
  font-size:14px;color:var(--navy);outline:none;transition:border-color var(--transition);
  background:#fff;
}
.form-field input:focus,.form-field select:focus,.form-field textarea:focus{border-color:var(--accent)}
.form-field textarea{resize:vertical;min-height:80px}
.eoi-disclaimer{
  padding:14px 16px;background:var(--silver-xlight);border-radius:var(--radius-sm);
  font-size:11px;color:var(--text-light);margin:16px 0;line-height:1.5;
}
.btn-submit{
  width:100%;padding:16px;background:var(--accent);color:#fff;border:none;
  border-radius:var(--radius);font-size:15px;font-weight:700;
  letter-spacing:0.5px;transition:all var(--transition);
}
.btn-submit:hover{background:var(--accent-dark);transform:translateY(-1px)}
.success-state{
  text-align:center;padding:40px 20px;display:none;
}
.success-state.visible{display:block}
.eoi-form-content.hidden{display:none}
.success-icon{font-size:56px;margin-bottom:16px}
.success-state h3{font-size:22px;font-weight:800;color:var(--navy);margin-bottom:8px}
.success-state p{font-size:14px;color:var(--text-light);max-width:400px;margin:0 auto}

/* ── Shared Utilities ── */
.section-divider{height:1px;background:var(--silver-xlight);margin:8px 0}
.empty-state{text-align:center;padding:48px 20px;color:var(--text-xlight)}
.empty-state .icon{font-size:48px;margin-bottom:12px}
.empty-state p{font-size:14px}
.tag{
  display:inline-flex;align-items:center;gap:4px;
  background:var(--silver-xlight);color:var(--text-mid);
  padding:3px 8px;border-radius:20px;font-size:10px;font-weight:600;
}
.validation-error{
  background:#FEF2F2;border:1px solid #FECACA;border-radius:var(--radius-sm);
  padding:10px 14px;font-size:12px;color:var(--red);margin-bottom:12px;display:none;
}
.validation-error.visible{display:block}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--silver);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--silver)}

/* ── Mobile ── */
@media(max-width:900px){
  .customize-layout{grid-template-columns:1fr}
  .pricing-sidebar{position:static}
  .project-grid{grid-template-columns:1fr}
  .summary-layout{grid-template-columns:1fr}
  .summary-total-card{flex-direction:column;gap:16px;text-align:center}
  .summary-total-right{text-align:center}
  .form-grid{grid-template-columns:1fr}
  .inclusions-grid{grid-template-columns:1fr}
  .facade-grid{grid-template-columns:1fr 1fr}
}
@media(max-width:600px){
  .top-bar{padding:0 16px}
  .main-content{padding:16px}
  .nav-footer{padding:14px 16px}
  .progress-bar-wrap{padding:0 16px}
  .prog-step-label{display:none}
  .prog-step{min-width:48px;flex:none}
  .facade-grid{grid-template-columns:1fr 1fr}
  .builder-grid{grid-template-columns:1fr}
  .design-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- ── Password Gate ── -->
<div id="auth-gate">
  <div class="gate-wrap">
    <div class="gate-logo">PX</div>
    <div class="gate-box">
      <div class="gate-badge">⚠ Confidential — Consultant Access Only</div>
      <h2>House &amp; Land Design Portal</h2>
      <p class="gate-sub">Enter your access code to continue</p>
      <input type="password" id="gate-pass" class="gate-input" placeholder="Access Code" autocomplete="off" />
      <button class="gate-btn" onclick="checkAccess()">Access Portal</button>
    </div>
    <div class="gate-footer">ProjX Australia &mdash; Confidential &amp; Not For Distribution</div>
  </div>
</div>

<!-- ── App ── -->
<div id="app">

  <!-- Top Bar -->
  <div class="top-bar">
    <div class="top-bar-left">
      <div class="top-logo">PX</div>
      <div>
        <div class="top-title">House &amp; Land Design Portal <span>— Buyer Experience V1</span></div>
      </div>
    </div>
    <div class="top-bar-right">
      <div class="confidential-badge">⚠ Consultant Access Only</div>
      <div class="top-step-label" id="step-label">Step 1 of 6</div>
    </div>
  </div>

  <!-- Progress Steps -->
  <div class="progress-bar-wrap">
    <div class="progress-steps">
      <div class="prog-step active" id="prog-1">
        <div class="prog-step-num">1</div>
        <div class="prog-step-label">Project</div>
      </div>
      <div class="prog-step" id="prog-2">
        <div class="prog-step-num">2</div>
        <div class="prog-step-label">Lot</div>
      </div>
      <div class="prog-step" id="prog-3">
        <div class="prog-step-num">3</div>
        <div class="prog-step-label">Builders</div>
      </div>
      <div class="prog-step" id="prog-4">
        <div class="prog-step-num">4</div>
        <div class="prog-step-label">Designs</div>
      </div>
      <div class="prog-step" id="prog-5">
        <div class="prog-step-num">5</div>
        <div class="prog-step-label">Customise</div>
      </div>
      <div class="prog-step" id="prog-6">
        <div class="prog-step-num">6</div>
        <div class="prog-step-label">Submit EOI</div>
      </div>
    </div>
  </div>

  <!-- ── STEP 1: Project Selection ── -->
  <div class="main-content">
    <div class="step-pane active" id="step-1-pane">
      <div class="step-header">
        <h2>Choose Your Project</h2>
        <p>Select the community where you'd like to build your new home. Each project offers a unique lifestyle and location.</p>
      </div>
      <div class="validation-error" id="err-1">Please select a project to continue.</div>
      <div class="project-grid" id="project-grid"></div>
    </div>

    <!-- ── STEP 2: Lot Selection ── -->
    <div class="step-pane" id="step-2-pane">
      <div class="step-header">
        <h2>Select Your Lot</h2>
        <p>Browse available lots in your chosen project. Click a lot to select it and proceed to builder selection.</p>
      </div>
      <div class="validation-error" id="err-2">Please select a lot to continue.</div>
      <div class="lot-controls">
        <div>
          <div class="filter-label" style="margin-bottom:4px">Sort By</div>
          <select id="lot-sort" onchange="renderLots()">
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="size-asc">Size: Small to Large</option>
            <option value="size-desc">Size: Large to Small</option>
          </select>
        </div>
        <div>
          <div class="filter-label" style="margin-bottom:4px">Status</div>
          <select id="lot-filter-status" onchange="renderLots()">
            <option value="all">All Lots</option>
            <option value="Available">Available Only</option>
          </select>
        </div>
        <div>
          <div class="filter-label" style="margin-bottom:4px">Max Price</div>
          <select id="lot-filter-price" onchange="renderLots()">
            <option value="0">Any Price</option>
            <option value="250000">Under $250k</option>
            <option value="300000">Under $300k</option>
            <option value="350000">Under $350k</option>
            <option value="400000">Under $400k</option>
            <option value="450000">Under $450k</option>
            <option value="500000">Under $500k</option>
          </select>
        </div>
      </div>
      <div class="lot-grid" id="lot-grid"></div>
    </div>

    <!-- ── STEP 3: Builder Selection ── -->
    <div class="step-pane" id="step-3-pane">
      <div class="step-header">
        <h2>Select Your Builder(s)</h2>
        <p>Choose up to 2 ProjX partner builders to explore. Each brings a distinct style, price point, and build timeline.</p>
      </div>
      <div class="validation-error" id="err-3">Please select at least one builder to continue.</div>
      <div class="builder-hint">Select up to <strong>2 builders</strong> to compare designs side by side</div>
      <div class="builder-grid" id="builder-grid"></div>
    </div>

    <!-- ── STEP 4: Design Browsing ── -->
    <div class="step-pane" id="step-4-pane">
      <div class="step-header">
        <h2>Browse Home Designs</h2>
        <p>Designs shown are compatible with your selected lot. Shortlist up to 2 designs to customise and compare.</p>
      </div>
      <div class="validation-error" id="err-4">Please shortlist at least one design to continue.</div>
      <div id="frontage-notice" class="frontage-notice" style="display:none"></div>
      <div class="design-filter-bar">
        <span style="font-size:12px;font-weight:600;color:var(--text-light)">Filter:</span>
        <button class="filter-chip active" onclick="filterDesigns('all',this)">All Designs</button>
        <button class="filter-chip" onclick="filterDesigns('compatible',this)">Fits My Lot</button>
        <button class="filter-chip" onclick="filterDesigns('4bed',this)">4+ Bed</button>
        <button class="filter-chip" onclick="filterDesigns('5bed',this)">5 Bed</button>
        <span id="design-count-label" style="font-size:11px;color:var(--text-xlight);margin-left:auto"></span>
      </div>
      <div class="design-grid" id="design-grid"></div>
    </div>

    <!-- ── STEP 5: Customise ── -->
    <div class="step-pane" id="step-5-pane">
      <div class="step-header">
        <h2>Customise Your Home</h2>
        <p>Personalise your selected design with your choice of facade, inclusions package, and optional upgrades.</p>
      </div>
      <div class="customize-layout">
        <div class="customize-main">
          <!-- Facade -->
          <div class="customize-section">
            <div class="customize-section-title">Facade Selection</div>
            <div class="facade-grid" id="facade-grid"></div>
          </div>
          <!-- Inclusions -->
          <div class="customize-section">
            <div class="customize-section-title">Inclusions Package</div>
            <div class="inclusions-grid" id="inclusions-grid"></div>
          </div>
          <!-- Upgrades -->
          <div class="customize-section">
            <div class="customize-section-title">Optional Upgrades</div>
            <div class="upgrades-grid" id="upgrades-grid"></div>
          </div>
        </div>
        <!-- Pricing Sidebar -->
        <div class="pricing-sidebar">
          <h3>Indicative Pricing</h3>
          <div class="pricing-design-preview" id="pricing-design-preview"></div>
          <div class="pricing-breakdown">
            <div class="pricing-row">
              <span class="pricing-row-label">Land</span>
              <span class="pricing-row-val" id="price-land">—</span>
            </div>
            <div class="pricing-row">
              <span class="pricing-row-label">Build (Base)</span>
              <span class="pricing-row-val" id="price-build">—</span>
            </div>
            <div class="pricing-row">
              <span class="pricing-row-label">Facade Upgrade</span>
              <span class="pricing-row-val" id="price-facade">Included</span>
            </div>
            <div class="pricing-row">
              <span class="pricing-row-label">Inclusions</span>
              <span class="pricing-row-val" id="price-inclusions">Standard</span>
            </div>
            <div class="pricing-row">
              <span class="pricing-row-label">Upgrades</span>
              <span class="pricing-row-val" id="price-upgrades">$0</span>
            </div>
          </div>
          <div class="pricing-total">
            <div class="label">Total Package From</div>
            <div class="amount" id="price-total">—</div>
            <div class="qualifier">Indicative only — subject to final contract</div>
          </div>
          <div style="margin-top:12px;font-size:10px;color:rgba(203,210,216,0.5);line-height:1.5">
            All pricing is indicative only. Final pricing is subject to site costs, council requirements, and builder contracts. Speak with your ProjX consultant.
          </div>
        </div>
      </div>
    </div>

    <!-- ── STEP 6: Summary & EOI ── -->
    <div class="step-pane" id="step-6-pane">
      <div class="step-header">
        <h2>Review &amp; Submit EOI</h2>
        <p>Review your selections below and submit your Expression of Interest. Your ProjX consultant will be in touch to finalise the details.</p>
      </div>

      <div class="summary-total-card">
        <div class="summary-total-left">
          <div class="label">Total Indicative Package Price</div>
          <div class="amount" id="summary-total-price">—</div>
          <div class="qualifier">Land + Build + Customisations (indicative)</div>
        </div>
        <div class="summary-total-right">
          <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px">Your Project</div>
          <div id="summary-project-name" style="font-size:18px;font-weight:800;color:#fff"></div>
          <div id="summary-suburb-name" style="font-size:13px;color:var(--silver);margin-top:2px"></div>
        </div>
      </div>

      <div class="summary-layout">
        <div class="summary-card">
          <h3>Lot Details</h3>
          <div id="summary-lot-details"></div>
        </div>
        <div class="summary-card">
          <h3>Home Design</h3>
          <div id="summary-design-details"></div>
        </div>
        <div class="summary-card">
          <h3>Selected Builders</h3>
          <div id="summary-builders"></div>
        </div>
        <div class="summary-card">
          <h3>Customisations</h3>
          <div id="summary-customisations"></div>
        </div>
      </div>

      <div class="eoi-section">
        <div class="eoi-form-content" id="eoi-form-content">
          <h3>Expression of Interest</h3>
          <p>Complete the form below and your dedicated ProjX consultant will contact you to progress your EOI.</p>
          <div class="form-grid">
            <div class="form-field">
              <label>First Name *</label>
              <input type="text" id="eoi-fname" placeholder="First name" required />
            </div>
            <div class="form-field">
              <label>Last Name *</label>
              <input type="text" id="eoi-lname" placeholder="Last name" required />
            </div>
            <div class="form-field">
              <label>Email Address *</label>
              <input type="email" id="eoi-email" placeholder="your@email.com" required />
            </div>
            <div class="form-field">
              <label>Phone Number *</label>
              <input type="tel" id="eoi-phone" placeholder="0400 000 000" required />
            </div>
            <div class="form-field">
              <label>Preferred Contact Time</label>
              <select id="eoi-contact-time">
                <option>Anytime</option>
                <option>Morning (8am–12pm)</option>
                <option>Afternoon (12pm–5pm)</option>
                <option>Evening (5pm–7pm)</option>
              </select>
            </div>
            <div class="form-field">
              <label>How did you hear about us?</label>
              <select id="eoi-source">
                <option>Via ProjX Consultant</option>
                <option>Website</option>
                <option>Social Media</option>
                <option>Referral</option>
                <option>Other</option>
              </select>
            </div>
            <div class="form-field full">
              <label>Additional Notes</label>
              <textarea id="eoi-notes" placeholder="Any questions or additional requirements?"></textarea>
            </div>
          </div>
          <div class="eoi-disclaimer">
            By submitting this Expression of Interest, you acknowledge that all pricing shown is indicative only and subject to change. This EOI does not constitute a binding contract. A ProjX consultant will contact you to discuss formal contracts and final pricing.
          </div>
          <div class="validation-error" id="err-6">Please fill in all required fields.</div>
          <button class="btn-submit" onclick="submitEOI()">Submit Expression of Interest →</button>
        </div>
        <div class="success-state" id="eoi-success">
          <div class="success-icon">✅</div>
          <h3>EOI Submitted Successfully!</h3>
          <p>Thank you! Your ProjX consultant will be in touch within 1 business day to finalise your Expression of Interest and discuss next steps.</p>
          <p style="margin-top:16px;font-size:12px;color:var(--text-xlight)">Reference: <strong id="eoi-ref"></strong></p>
        </div>
      </div>
    </div>
  </div><!-- /main-content -->

  <!-- Nav Footer -->
  <div class="nav-footer">
    <div class="nav-left">
      <button class="btn-back" id="btn-back" onclick="prevStep()" style="display:none">← Back</button>
      <span class="nav-info" id="nav-info"></span>
    </div>
    <div class="nav-right">
      <button class="btn-next" id="btn-next" onclick="nextStep()">
        Continue
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>
  </div>

</div><!-- /app -->

<script>
// ── Injected Data ──────────────────────────────────────────────────────────────
const OAKLAND_LOTS = __OAKLAND_DATA__;
const ALL_LOTS = {
  oakland: OAKLAND_LOTS,
  woodchester: __WOODCHESTER_DATA__,
  ooranya: __OORANYA_DATA__
};
const BUILD_DATE = "__BUILD_DATE__";

// ── Static App Data ────────────────────────────────────────────────────────────
const PROJECTS = [
  {
    id: 'oakland',
    name: 'Oakland Estate',
    suburb: 'Beaudesert',
    region: 'South East Queensland',
    minPrice: 285000,
    lots: null, // filled from OAKLAND_LOTS
    status: 'Selling Now',
    emoji: '🌿',
    features: ['H&L Packages', 'Stage 2 Now Selling', 'NBN Connected'],
    stats: { lots: null, stages: 2, distance: '55km to Brisbane' }
  },
  {
    id: 'woodchester',
    name: 'Woodchester',
    suburb: 'Gatton',
    region: 'Lockyer Valley',
    minPrice: 228000,
    lots: __WOODCHESTER_DATA__,
    status: 'Selling Now',
    emoji: '🌾',
    features: ['Rural Residential', 'Large Acreage Lots', 'Peaceful Lifestyle'],
    stats: { lots: 6, stages: 2, distance: '80km to Brisbane' }
  },
  {
    id: 'ooranya',
    name: 'Ooranya',
    suburb: 'Coomera',
    region: 'Gold Coast',
    minPrice: 375000,
    lots: __OORANYA_DATA__,
    status: 'Now Selling',
    emoji: '🏙️',
    features: ['Gold Coast Location', 'Premium H&L', 'Coomera Hub Nearby'],
    stats: { lots: 6, stages: 2, distance: '45km to Brisbane' }
  }
];

const BUILDERS = [
  {
    id: 'nexgen',
    name: 'NexGen Homes',
    tagline: 'Smart homes, smarter value',
    tier: 'Entry',
    tierClass: 'tier-entry',
    priceRange: '$250k – $350k',
    buildTime: '7–9 months',
    style: 'Contemporary & functional',
    emoji: '🏠',
    color: '#059669',
    intro: 'NexGen delivers quality entry-level builds with clever design and fast timelines.'
  },
  {
    id: 'avia',
    name: 'AVIA Homes',
    tagline: 'Design-led homes, built to last',
    tier: 'Entry–Mid',
    tierClass: 'tier-entry-mid',
    priceRange: '$280k – $380k',
    buildTime: '8–10 months',
    style: 'Modern & design-led',
    emoji: '🏡',
    color: '#1D4ED8',
    intro: 'AVIA blends contemporary design with practical floor plans for growing families.'
  },
  {
    id: 'homecorp',
    name: 'Homecorp',
    tagline: 'More space, more life',
    tier: 'Mid',
    tierClass: 'tier-mid',
    priceRange: '$350k – $450k',
    buildTime: '9–12 months',
    style: 'Spacious family homes',
    emoji: '🏘️',
    color: '#6D28D9',
    intro: 'Homecorp specialises in generous family homes with premium inclusions as standard.'
  },
  {
    id: 'coral',
    name: 'Coral Homes',
    tagline: 'Crafted for Queensland living',
    tier: 'Mid–Premium',
    tierClass: 'tier-mid-premium',
    priceRange: '$400k – $550k',
    buildTime: '10–14 months',
    style: 'Premium Queensland lifestyle',
    emoji: '🌺',
    color: '#9D174D',
    intro: 'Coral Homes is renowned for premium finishes and designs built for the Queensland climate.'
  },
  {
    id: 'bold',
    name: 'Bold Living',
    tagline: 'Where architecture meets lifestyle',
    tier: 'Premium',
    tierClass: 'tier-premium',
    priceRange: '$500k+',
    buildTime: '12–16 months',
    style: 'Architectural premium homes',
    emoji: '✨',
    color: '#B45309',
    intro: 'Bold Living creates architectural masterpieces for buyers who demand the best.'
  }
];

const DESIGNS = [
  // NexGen
  { id: 'ng1', builder: 'nexgen', name: 'Vibe 18', bed: 3, bath: 2, car: 1, study: 0, sqm: 168, minFrontage: 10, basePrice: 258000, highlight: 'Compact & clever' },
  { id: 'ng2', builder: 'nexgen', name: 'Edge 20', bed: 4, bath: 2, car: 2, study: 0, sqm: 188, minFrontage: 12, basePrice: 278000, highlight: 'Best-selling design' },
  { id: 'ng3', builder: 'nexgen', name: 'Flow 24', bed: 4, bath: 2, car: 2, study: 0, sqm: 210, minFrontage: 12, basePrice: 299000, highlight: 'Open-plan living' },
  // AVIA
  { id: 'av1', builder: 'avia', name: 'Gemini 220', bed: 4, bath: 2, car: 2, study: 0, sqm: 220, minFrontage: 12, basePrice: 315000, highlight: 'Family favourite' },
  { id: 'av2', builder: 'avia', name: 'Prism 240', bed: 4, bath: 2, car: 2, study: 1, sqm: 240, minFrontage: 14, basePrice: 348000, highlight: 'With home office' },
  { id: 'av3', builder: 'avia', name: 'Apex 260', bed: 4, bath: 2, car: 2, study: 0, sqm: 258, minFrontage: 14, basePrice: 365000, highlight: 'Entertainer\'s layout' },
  // Homecorp
  { id: 'hc1', builder: 'homecorp', name: 'Sherwood 28', bed: 4, bath: 2, car: 2, study: 0, sqm: 275, minFrontage: 14, basePrice: 378000, highlight: 'Generous living' },
  { id: 'hc2', builder: 'homecorp', name: 'Ridgeline 32', bed: 4, bath: 3, car: 2, study: 0, sqm: 318, minFrontage: 16, basePrice: 425000, highlight: '3 bathrooms' },
  { id: 'hc3', builder: 'homecorp', name: 'Bridgewater 35', bed: 5, bath: 3, car: 2, study: 0, sqm: 348, minFrontage: 16, basePrice: 445000, highlight: '5-bedroom family' },
  // Coral
  { id: 'cl1', builder: 'coral', name: 'Essence 310', bed: 4, bath: 2, car: 2, study: 1, sqm: 312, minFrontage: 16, basePrice: 455000, highlight: 'Alfresco focused' },
  { id: 'cl2', builder: 'coral', name: 'Crest 340', bed: 4, bath: 3, car: 3, study: 0, sqm: 338, minFrontage: 18, basePrice: 495000, highlight: 'Triple garage' },
  { id: 'cl3', builder: 'coral', name: 'Horizon 370', bed: 5, bath: 3, car: 3, study: 1, sqm: 372, minFrontage: 18, basePrice: 525000, highlight: 'Ultimate family home' },
  // Bold Living
  { id: 'bl1', builder: 'bold', name: 'Magnolia 390', bed: 4, bath: 3, car: 2, study: 1, sqm: 392, minFrontage: 18, basePrice: 545000, highlight: 'Architectural icon' },
  { id: 'bl2', builder: 'bold', name: 'Sovereign 420', bed: 5, bath: 3, car: 3, study: 1, sqm: 418, minFrontage: 20, basePrice: 565000, highlight: 'Statement living' },
  { id: 'bl3', builder: 'bold', name: 'Prestige 450', bed: 5, bath: 4, car: 3, study: 0, sqm: 452, minFrontage: 20, basePrice: 620000, highlight: 'Pinnacle of luxury' }
];

const FACADES = [
  { id: 'standard', name: 'Standard', description: 'Classic rendered facade', premium: 0, color: '#64748B' },
  { id: 'modern', name: 'Modern', description: 'Clean lines, feature cladding', premium: 8500, color: '#1E40AF' },
  { id: 'hamptons', name: 'Hamptons', description: 'Coastal elegance, weatherboard detail', premium: 12000, color: '#0F766E' },
  { id: 'contemporary', name: 'Contemporary', description: 'Bold angles, mixed materials', premium: 7500, color: '#7C3AED' }
];

const INCLUSIONS = [
  {
    id: 'standard',
    name: 'Standard',
    description: 'Quality inclusions that exceed industry standards. Includes stone-look benchtops, stainless appliances, and LED lighting throughout.',
    premium: 0
  },
  {
    id: 'premium',
    name: 'Premium',
    description: 'Elevated finishes with 20mm stone benchtops, premium appliance package, upgraded carpet and tiles, and feature walls.',
    premium: 28000
  },
  {
    id: 'luxury',
    name: 'Luxury',
    description: 'Top-tier finishes. 40mm stone, Bosch/Smeg appliance suite, engineered timber floors, custom cabinetry, and smart home pre-wire.',
    premium: 62000
  }
];

const UPGRADES = [
  { id: 'ac', icon: '❄️', name: 'Ducted Air Conditioning', description: '7-zone ducted reverse-cycle system', price: 12500 },
  { id: 'stone', icon: '🪨', name: 'Stone Benchtops', description: '20mm engineered stone throughout', price: 4500 },
  { id: 'ceilings', icon: '📐', name: '2700mm Ceilings', description: 'Elevated ceiling heights throughout', price: 3800 },
  { id: 'flooring', icon: '🪵', name: 'Upgraded Flooring', description: 'Luxury vinyl plank throughout living areas', price: 6200 },
  { id: 'solar', icon: '☀️', name: 'Solar System (6.6kW)', description: '6.6kW solar + monitoring system', price: 7900 },
  { id: 'theatre', icon: '🎬', name: 'Theatre Room Setup', description: 'Acoustic walls, recessed lighting, pre-wire', price: 8500 },
  { id: 'butler', icon: '🍽️', name: "Butler's Pantry", description: 'Full butler\'s pantry with sink and storage', price: 11000 },
  { id: 'alfresco', icon: '🌿', name: 'Alfresco Extension', description: 'Extended covered outdoor entertaining area', price: 18500 }
];

// ── App State ──────────────────────────────────────────────────────────────────
const state = {
  step: 1,
  project: null,
  lot: null,
  builders: [],
  design: null,
  facade: 'standard',
  inclusions: 'standard',
  upgrades: [],
  designFilter: 'all'
};

// ── Auth ───────────────────────────────────────────────────────────────────────
function checkAccess() {
  const input = document.getElementById('gate-pass');
  if (input.value === 'LV9') {
    document.getElementById('auth-gate').classList.add('hidden');
    document.getElementById('app').classList.add('visible');
    sessionStorage.setItem('design-portal-auth', '1');
    initApp();
  } else {
    input.classList.add('error');
    input.value = '';
    setTimeout(() => input.classList.remove('error'), 500);
  }
}
document.getElementById('gate-pass').addEventListener('keydown', e => {
  if (e.key === 'Enter') checkAccess();
});
if (sessionStorage.getItem('design-portal-auth') === '1') {
  document.getElementById('auth-gate').classList.add('hidden');
  document.getElementById('app').classList.add('visible');
  initApp();
}

// ── Formatters ─────────────────────────────────────────────────────────────────
function fmt(n) {
  return '$' + Math.round(n).toLocaleString('en-AU');
}

// ── App Init ───────────────────────────────────────────────────────────────────
function initApp() {
  // Enrich projects with lot counts
  PROJECTS[0].lots = OAKLAND_LOTS;
  PROJECTS[0].stats.lots = OAKLAND_LOTS.length;
  const oaklandPrices = OAKLAND_LOTS.filter(l => l.price > 0).map(l => l.price);
  if (oaklandPrices.length) PROJECTS[0].minPrice = Math.min(...oaklandPrices);

  renderProjects();
  renderBuilders();
  updateNav();
}

// ── Step Navigation ────────────────────────────────────────────────────────────
function goToStep(n) {
  document.getElementById('step-' + state.step + '-pane').classList.remove('active');
  document.getElementById('prog-' + state.step).classList.remove('active');
  if (n > state.step) document.getElementById('prog-' + state.step).classList.add('done');
  else document.getElementById('prog-' + state.step).classList.remove('done');
  state.step = n;
  document.getElementById('step-' + state.step + '-pane').classList.add('active');
  updateProgressSteps();
  updateNav();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgressSteps() {
  for (let i = 1; i <= 6; i++) {
    const el = document.getElementById('prog-' + i);
    el.classList.remove('active', 'done');
    if (i < state.step) el.classList.add('done');
    else if (i === state.step) el.classList.add('active');
  }
}

function nextStep() {
  if (!validateStep(state.step)) return;
  if (state.step === 2) renderBuilders();
  if (state.step === 3) renderDesigns();
  if (state.step === 5) renderSummary();
  goToStep(state.step + 1);
  if (state.step === 5) renderCustomize();
}

function prevStep() {
  goToStep(state.step - 1);
}

function updateNav() {
  const back = document.getElementById('btn-back');
  const next = document.getElementById('btn-next');
  const label = document.getElementById('step-label');
  back.style.display = state.step > 1 ? 'block' : 'none';
  label.textContent = 'Step ' + state.step + ' of 6';
  if (state.step === 6) {
    next.style.display = 'none';
  } else {
    next.style.display = 'flex';
    next.textContent = state.step === 5 ? 'Review & Submit' : 'Continue';
    const svg = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    next.innerHTML = (state.step === 5 ? 'Review & Submit' : 'Continue') + ' ' + svg;
  }
  updateNavInfo();
}

function updateNavInfo() {
  const info = document.getElementById('nav-info');
  if (state.step === 2 && state.lot) info.textContent = '✓ ' + state.lot.name + ' selected';
  else if (state.step === 3) info.textContent = state.builders.length + '/2 builders selected';
  else if (state.step === 4) info.textContent = state.design ? '✓ ' + state.design.name + ' shortlisted' : '';
  else info.textContent = '';
}

function validateStep(step) {
  const hideErr = id => document.getElementById(id).classList.remove('visible');
  const showErr = id => document.getElementById(id).classList.add('visible');
  if (step === 1) {
    hideErr('err-1');
    if (!state.project) { showErr('err-1'); return false; }
  }
  if (step === 2) {
    hideErr('err-2');
    if (!state.lot) { showErr('err-2'); return false; }
  }
  if (step === 3) {
    hideErr('err-3');
    if (state.builders.length === 0) { showErr('err-3'); return false; }
  }
  if (step === 4) {
    hideErr('err-4');
    if (!state.design) { showErr('err-4'); return false; }
  }
  return true;
}

// ── STEP 1: Projects ───────────────────────────────────────────────────────────
function renderProjects() {
  const grid = document.getElementById('project-grid');
  grid.innerHTML = PROJECTS.map(p => {
    const lots = ALL_LOTS[p.id] || [];
    const avail = lots.filter(l => l.availability === 'Available').length;
    const minP = lots.filter(l => l.price > 0).map(l => l.price);
    const displayMin = minP.length ? Math.min(...minP) : p.minPrice;
    return `
    <div class="project-card ${state.project && state.project.id === p.id ? 'selected' : ''}" onclick="selectProject('${p.id}')">
      <div class="project-hero">
        <div class="project-status-chip">${p.status}</div>
        <div class="project-hero-icon">${p.emoji}</div>
        <div class="project-hero-text">
          <div class="suburb">${p.suburb}, ${p.region}</div>
          <div class="name">${p.name}</div>
        </div>
      </div>
      <div class="project-body">
        <div class="project-stats">
          <div class="project-stat">
            <div class="val">${avail || lots.length}</div>
            <div class="lbl">Lots Avail</div>
          </div>
          <div class="project-stat">
            <div class="val">${p.stats.stages}</div>
            <div class="lbl">Stages</div>
          </div>
          <div class="project-stat">
            <div class="val">${p.stats.distance.split(' ')[0]}</div>
            <div class="lbl">${p.stats.distance.split(' ').slice(1).join(' ')}</div>
          </div>
        </div>
        <div class="project-price">Land from <strong>${fmt(displayMin)}</strong></div>
        <div class="project-features">
          ${p.features.map(f => `<span class="project-feature">${f}</span>`).join('')}
        </div>
        <button class="project-select-btn">${state.project && state.project.id === p.id ? '✓ Selected' : 'Select Project'}</button>
      </div>
    </div>`;
  }).join('');
}

function selectProject(id) {
  state.project = PROJECTS.find(p => p.id === id);
  state.lot = null;
  state.builders = [];
  state.design = null;
  document.getElementById('err-1').classList.remove('visible');
  renderProjects();
  renderLots();
  updateNav();
}

// ── STEP 2: Lots ──────────────────────────────────────────────────────────────
function renderLots() {
  const grid = document.getElementById('lot-grid');
  if (!state.project) { grid.innerHTML = '<div class="no-lots">Select a project first.</div>'; return; }
  let lots = (ALL_LOTS[state.project.id] || []).slice();

  const sort = document.getElementById('lot-sort').value;
  const filterStatus = document.getElementById('lot-filter-status').value;
  const filterPrice = parseInt(document.getElementById('lot-filter-price').value) || 0;

  if (filterStatus !== 'all') lots = lots.filter(l => l.availability === filterStatus);
  if (filterPrice > 0) lots = lots.filter(l => l.price <= filterPrice);

  if (sort === 'price-asc') lots.sort((a, b) => a.price - b.price);
  else if (sort === 'price-desc') lots.sort((a, b) => b.price - a.price);
  else if (sort === 'size-asc') lots.sort((a, b) => a.lot_size - b.lot_size);
  else if (sort === 'size-desc') lots.sort((a, b) => b.lot_size - a.lot_size);

  if (!lots.length) {
    grid.innerHTML = '<div class="no-lots"><div class="icon">🔍</div><p>No lots match your filters. Try adjusting the criteria above.</p></div>';
    return;
  }

  grid.innerHTML = lots.map(l => {
    const isSelected = state.lot && state.lot.id === l.id;
    const frontageDisplay = l.lot_size > 1000 ? l.frontage + 'm width' : l.frontage + 'm frontage';
    return `
    <div class="lot-card ${isSelected ? 'selected' : ''}" onclick="selectLot('${l.id}')">
      <div class="lot-card-head">
        <div>
          <div class="lot-name">${l.name}</div>
          <div class="lot-stage">${l.stage || 'Stage 1'} · ${l.type || 'H&L'}</div>
        </div>
        <div class="lot-avail ${l.availability}">${l.availability}</div>
      </div>
      <div class="lot-specs">
        <div class="lot-spec"><div class="sv">${l.lot_size ? l.lot_size.toLocaleString() : '—'}</div><div class="sl">sqm</div></div>
        <div class="lot-spec"><div class="sv">${frontageDisplay}</div><div class="sl">frontage est.</div></div>
      </div>
      <div class="lot-price-row">
        <div class="lot-price">${l.price ? fmt(l.price) : 'POA'}</div>
        <button class="lot-select-btn">${isSelected ? '✓ Selected' : 'Select'}</button>
      </div>
    </div>`;
  }).join('');
  updateNavInfo();
}

function selectLot(id) {
  const lots = ALL_LOTS[state.project.id] || [];
  state.lot = lots.find(l => l.id === id);
  state.design = null;
  document.getElementById('err-2').classList.remove('visible');
  renderLots();
  updateNavInfo();
}

// ── STEP 3: Builders ──────────────────────────────────────────────────────────
function renderBuilders() {
  const grid = document.getElementById('builder-grid');
  grid.innerHTML = BUILDERS.map(b => {
    const isSelected = state.builders.includes(b.id);
    const isDisabled = !isSelected && state.builders.length >= 2;
    return `
    <div class="builder-card ${isSelected ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}" onclick="toggleBuilder('${b.id}')">
      <div class="builder-check">
        ${isSelected ? '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7l4 4 6-6" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' : ''}
      </div>
      <div class="builder-logo-area" style="background:${b.color}">${b.emoji}</div>
      <div class="builder-name">${b.name}</div>
      <div class="builder-tagline">${b.tagline}</div>
      <div class="builder-attrs">
        <div class="builder-attr">
          <div class="builder-attr-icon">💰</div>
          <span class="builder-attr-label">Build Price</span>
          <span class="builder-attr-val">${b.priceRange}</span>
        </div>
        <div class="builder-attr">
          <div class="builder-attr-icon">🏗️</div>
          <span class="builder-attr-label">Build Time</span>
          <span class="builder-attr-val">${b.buildTime}</span>
        </div>
        <div class="builder-attr">
          <div class="builder-attr-icon">🎨</div>
          <span class="builder-attr-label">Style</span>
          <span class="builder-attr-val" style="font-size:11px">${b.style}</span>
        </div>
      </div>
      <div class="builder-tier ${b.tierClass}">${b.tier}</div>
    </div>`;
  }).join('');
}

function toggleBuilder(id) {
  if (state.builders.includes(id)) {
    state.builders = state.builders.filter(b => b !== id);
  } else if (state.builders.length < 2) {
    state.builders.push(id);
  }
  document.getElementById('err-3').classList.remove('visible');
  renderBuilders();
  updateNavInfo();
}

// ── STEP 4: Designs ───────────────────────────────────────────────────────────
function renderDesigns() {
  const grid = document.getElementById('design-grid');
  const notice = document.getElementById('frontage-notice');
  const frontage = state.lot ? state.lot.frontage : 99;

  let designs = DESIGNS.filter(d => state.builders.includes(d.builder));

  if (state.lot) {
    notice.style.display = 'block';
    notice.innerHTML = `<strong>Your Lot:</strong> ${state.lot.name} — ${state.lot.lot_size}sqm, estimated ${frontage}m frontage. Designs requiring wider frontage are shown greyed out.`;
  }

  // Apply filter
  const filter = state.designFilter;
  if (filter === 'compatible') designs = designs.filter(d => d.minFrontage <= frontage);
  else if (filter === '4bed') designs = designs.filter(d => d.bed >= 4);
  else if (filter === '5bed') designs = designs.filter(d => d.bed >= 5);

  document.getElementById('design-count-label').textContent = designs.length + ' design' + (designs.length !== 1 ? 's' : '') + ' shown';

  if (!designs.length) {
    grid.innerHTML = '<div class="no-lots"><div class="icon" style="font-size:32px">🏠</div><p>No designs match your current filters. Try selecting different builders or adjusting filters.</p></div>';
    return;
  }

  grid.innerHTML = designs.map(d => {
    const builder = BUILDERS.find(b => b.id === d.builder);
    const compatible = d.minFrontage <= frontage;
    const isSelected = state.design && state.design.id === d.id;
    let compatBadge = compatible
      ? (d.minFrontage === frontage ? '<span class="design-compat-badge tight">Tight Fit</span>' : '<span class="design-compat-badge fit">Fits Lot</span>')
      : '<span class="design-compat-badge no">Needs ' + d.minFrontage + 'm+</span>';

    const specs = [
      { icon: '🛏', val: d.bed + ' Bed' },
      { icon: '🚿', val: d.bath + ' Bath' },
      { icon: '🚗', val: d.car + ' Car' },
      ...(d.study ? [{ icon: '📚', val: 'Study' }] : [])
    ];

    return `
    <div class="design-card ${isSelected ? 'selected' : ''} ${!compatible ? 'incompatible' : ''}" onclick="selectDesign('${d.id}')">
      <div class="design-thumb">
        <div class="design-thumb-bg" style="background:linear-gradient(135deg,${builder.color}22 0%,${builder.color}44 100%)"></div>
        <div class="design-thumb-house" style="color:${builder.color}">🏠</div>
        ${compatBadge}
        <div class="design-thumb-overlay">
          <div class="design-thumb-name">${d.name}</div>
          <div class="design-thumb-builder">${builder.name}</div>
        </div>
      </div>
      <div class="design-body">
        <div class="design-specs">
          ${specs.map(s => `<div class="design-spec-pill"><span>${s.icon}</span><span>${s.val}</span></div>`).join('')}
        </div>
        <div class="design-footer">
          <div>
            <div class="design-price">From ${fmt(d.basePrice)}</div>
            <div class="design-size">${d.sqm}m² internal · Min ${d.minFrontage}m frontage</div>
          </div>
        </div>
        <button class="design-shortlist-btn">${isSelected ? '✓ Shortlisted' : 'Shortlist Design'}</button>
      </div>
    </div>`;
  }).join('');
  updateNavInfo();
}

function filterDesigns(filter, btn) {
  state.designFilter = filter;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  renderDesigns();
}

function selectDesign(id) {
  state.design = state.design && state.design.id === id ? null : DESIGNS.find(d => d.id === id);
  document.getElementById('err-4').classList.remove('visible');
  renderDesigns();
  updateNavInfo();
}

// ── STEP 5: Customize ─────────────────────────────────────────────────────────
function renderCustomize() {
  if (!state.design) return;
  const design = state.design;
  const builder = BUILDERS.find(b => b.id === design.builder);

  // Preview
  document.getElementById('pricing-design-preview').innerHTML = `
    <div class="pricing-design-name">${design.name}</div>
    <div class="pricing-design-sub">${builder.name} · ${design.bed}bd ${design.bath}ba ${design.car}car · ${design.sqm}m²</div>
  `;

  // Facades
  document.getElementById('facade-grid').innerHTML = FACADES.map(f => `
    <div class="facade-option ${state.facade === f.id ? 'selected' : ''}" onclick="selectFacade('${f.id}')">
      <div class="facade-thumb">
        <div class="facade-thumb-bg" style="background:${f.color}22"></div>
        <div class="facade-thumb-icon">🏠</div>
      </div>
      <div class="facade-name">${f.name}</div>
      <div class="facade-price">${f.premium === 0 ? 'Included' : '+' + fmt(f.premium)}</div>
    </div>`).join('');

  // Inclusions
  document.getElementById('inclusions-grid').innerHTML = INCLUSIONS.map(i => `
    <div class="incl-option ${state.inclusions === i.id ? 'selected' : ''}" onclick="selectInclusions('${i.id}')">
      <div class="incl-name">${i.name}</div>
      <div class="incl-desc">${i.description}</div>
      <div class="incl-price">${i.premium === 0 ? 'Included' : '+' + fmt(i.premium)}</div>
    </div>`).join('');

  // Upgrades
  document.getElementById('upgrades-grid').innerHTML = UPGRADES.map(u => `
    <div class="upgrade-item ${state.upgrades.includes(u.id) ? 'selected' : ''}" onclick="toggleUpgrade('${u.id}')">
      <div class="upgrade-check">
        ${state.upgrades.includes(u.id) ? '<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' : ''}
      </div>
      <div class="upgrade-icon">${u.icon}</div>
      <div class="upgrade-info">
        <div class="upgrade-name">${u.name}</div>
        <div class="upgrade-desc">${u.description}</div>
      </div>
      <div class="upgrade-price">+${fmt(u.price)}</div>
    </div>`).join('');

  updatePricing();
}

function selectFacade(id) {
  state.facade = id;
  renderCustomize();
}

function selectInclusions(id) {
  state.inclusions = id;
  renderCustomize();
}

function toggleUpgrade(id) {
  if (state.upgrades.includes(id)) state.upgrades = state.upgrades.filter(u => u !== id);
  else state.upgrades.push(id);
  renderCustomize();
}

function updatePricing() {
  const design = state.design;
  if (!design) return;
  const lot = state.lot;
  const facadeObj = FACADES.find(f => f.id === state.facade);
  const inclObj = INCLUSIONS.find(i => i.id === state.inclusions);
  const upgradeTotal = state.upgrades.reduce((sum, uid) => {
    const u = UPGRADES.find(u => u.id === uid);
    return sum + (u ? u.price : 0);
  }, 0);

  const landPrice = lot ? lot.price : 0;
  const buildBase = design.basePrice;
  const facadePremium = facadeObj ? facadeObj.premium : 0;
  const inclPremium = inclObj ? inclObj.premium : 0;
  const total = landPrice + buildBase + facadePremium + inclPremium + upgradeTotal;

  document.getElementById('price-land').textContent = lot ? fmt(landPrice) : 'TBC';
  document.getElementById('price-build').textContent = fmt(buildBase);
  document.getElementById('price-facade').textContent = facadePremium ? '+' + fmt(facadePremium) : 'Included';
  document.getElementById('price-inclusions').textContent = inclPremium ? '+' + fmt(inclPremium) : 'Standard';
  document.getElementById('price-upgrades').textContent = upgradeTotal ? '+' + fmt(upgradeTotal) : '$0';
  document.getElementById('price-total').textContent = fmt(total);
}

function getTotalPrice() {
  const design = state.design;
  if (!design) return 0;
  const lot = state.lot;
  const facadeObj = FACADES.find(f => f.id === state.facade);
  const inclObj = INCLUSIONS.find(i => i.id === state.inclusions);
  const upgradeTotal = state.upgrades.reduce((sum, uid) => {
    const u = UPGRADES.find(u => u.id === uid);
    return sum + (u ? u.price : 0);
  }, 0);
  return (lot ? lot.price : 0) + design.basePrice + (facadeObj ? facadeObj.premium : 0) + (inclObj ? inclObj.premium : 0) + upgradeTotal;
}

// ── STEP 6: Summary & EOI ──────────────────────────────────────────────────────
function renderSummary() {
  const design = state.design;
  const lot = state.lot;
  const project = state.project;
  const facadeObj = FACADES.find(f => f.id === state.facade);
  const inclObj = INCLUSIONS.find(i => i.id === state.inclusions);
  const total = getTotalPrice();

  document.getElementById('summary-total-price').textContent = fmt(total);
  document.getElementById('summary-project-name').textContent = project ? project.name : '';
  document.getElementById('summary-suburb-name').textContent = project ? project.suburb + ', QLD' : '';

  // Lot
  document.getElementById('summary-lot-details').innerHTML = lot ? `
    <div class="summary-row"><span class="s-label">Lot Name</span><span class="s-val">${lot.name}</span></div>
    <div class="summary-row"><span class="s-label">Land Size</span><span class="s-val">${lot.lot_size}m²</span></div>
    <div class="summary-row"><span class="s-label">Est. Frontage</span><span class="s-val">${lot.frontage}m</span></div>
    <div class="summary-row"><span class="s-label">Land Price</span><span class="s-val">${fmt(lot.price)}</span></div>
    <div class="summary-row"><span class="s-label">Status</span><span class="s-val">${lot.availability}</span></div>
  ` : '<p>No lot selected</p>';

  // Design
  const builder = design ? BUILDERS.find(b => b.id === design.builder) : null;
  document.getElementById('summary-design-details').innerHTML = design ? `
    <div class="summary-row"><span class="s-label">Design</span><span class="s-val">${design.name}</span></div>
    <div class="summary-row"><span class="s-label">Builder</span><span class="s-val">${builder ? builder.name : ''}</span></div>
    <div class="summary-row"><span class="s-label">Bedrooms</span><span class="s-val">${design.bed} Bed / ${design.bath} Bath / ${design.car} Car${design.study ? ' / Study' : ''}</span></div>
    <div class="summary-row"><span class="s-label">Internal Area</span><span class="s-val">${design.sqm}m²</span></div>
    <div class="summary-row"><span class="s-label">Base Build Price</span><span class="s-val">${fmt(design.basePrice)}</span></div>
  ` : '<p>No design selected</p>';

  // Builders
  const builderNames = state.builders.map(id => {
    const b = BUILDERS.find(b => b.id === id);
    return b ? `<div class="summary-builder-chip">${b.emoji} ${b.name}</div>` : '';
  }).join('');
  document.getElementById('summary-builders').innerHTML = `<div class="summary-builders-chips">${builderNames}</div>`;

  // Customisations
  const upgradesList = state.upgrades.map(uid => {
    const u = UPGRADES.find(u => u.id === uid);
    return u ? `<div class="summary-row"><span class="s-label">${u.name}</span><span class="s-val">+${fmt(u.price)}</span></div>` : '';
  }).join('');
  document.getElementById('summary-customisations').innerHTML = `
    <div class="summary-row"><span class="s-label">Facade</span><span class="s-val">${facadeObj ? facadeObj.name : ''}</span></div>
    <div class="summary-row"><span class="s-label">Inclusions</span><span class="s-val">${inclObj ? inclObj.name : ''}</span></div>
    ${upgradesList || '<div class="summary-row"><span class="s-label">Upgrades</span><span class="s-val">None selected</span></div>'}
  `;
}

function submitEOI() {
  const fname = document.getElementById('eoi-fname').value.trim();
  const lname = document.getElementById('eoi-lname').value.trim();
  const email = document.getElementById('eoi-email').value.trim();
  const phone = document.getElementById('eoi-phone').value.trim();

  if (!fname || !lname || !email || !phone) {
    document.getElementById('err-6').classList.add('visible');
    return;
  }
  document.getElementById('err-6').classList.remove('visible');

  // Generate ref
  const ref = 'EOI-' + Date.now().toString(36).toUpperCase();
  document.getElementById('eoi-ref').textContent = ref;
  document.getElementById('eoi-form-content').classList.add('hidden');
  document.getElementById('eoi-success').classList.add('visible');
  document.getElementById('btn-back').style.display = 'none';
}
</script>
</body>
</html>
"""


def build_html(oakland_lots):
    now = datetime.datetime.now().strftime("%d %b %Y")

    oakland_json = json.dumps(oakland_lots, ensure_ascii=False)
    woodchester_json = json.dumps(WOODCHESTER_LOTS, ensure_ascii=False)
    ooranya_json = json.dumps(OORANYA_LOTS, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("__OAKLAND_DATA__", oakland_json)
    html = html.replace("__WOODCHESTER_DATA__", woodchester_json)
    html = html.replace("__OORANYA_DATA__", ooranya_json)
    html = html.replace("__BUILD_DATE__", now)

    return html


def main():
    print("🏗  ProjX House & Land Design Portal — V1 Build")
    print("=" * 48)

    try:
        token = get_token()
        print("✓  Monday.com token loaded")
    except Exception as e:
        print(f"✗  {e}")
        sys.exit(1)

    print("→  Fetching Oakland Estate lots from Monday.com…", end="", flush=True)
    try:
        oakland_lots = fetch_oakland_lots(token)
        avail = sum(1 for l in oakland_lots if l["availability"] == "Available")
        print(f" done ({len(oakland_lots)} lots, {avail} available)")
    except Exception as e:
        print(f"\n✗  Failed to fetch lots: {e}")
        print("   Using empty Oakland data — check API token and board ID")
        oakland_lots = []

    print("→  Generating HTML…", end="", flush=True)
    html = build_html(oakland_lots)
    print(" done")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"✓  Written: {out_path} ({size_kb:.0f} KB)")
    print()
    print("📦 Summary")
    print(f"   Oakland lots:    {len(oakland_lots)}")
    print(f"   Woodchester:     {len(WOODCHESTER_LOTS)} (sample)")
    print(f"   Ooranya:         {len(OORANYA_LOTS)} (sample)")
    print(f"   Builders:        5")
    print(f"   Designs:         15")


if __name__ == "__main__":
    main()
