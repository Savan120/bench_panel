#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for


APP_TITLE = "Frappe Bench Control Panel"
SECRET_KEY = os.environ.get("BENCH_PANEL_SECRET_KEY", "change-this-secret-key")
PANEL_PASSWORD = os.environ.get("BENCH_PANEL_PASSWORD", "admin123")
SITE_PROTOCOL = os.environ.get("BENCH_SITE_PROTOCOL", "http")
DEFAULT_COMMON_SITE_CONFIG = "common_site_config.json"

app = Flask(__name__)
app.secret_key = SECRET_KEY


HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJAAAACQCAYAAADnRuK4AAAACXBIWXMAABYlAAAWJQFJUiTwAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAFNSURBVHgB7d2xNYRBFEDht45YFTQhU4pKKEUpG6EHAiU4h9QONbgC/+73BVPBPRPNezMDAAAAAAAAAAAAAAAAAAAA/9tuNubi6nrNCVhr7T9en27mnzsbCAREIiASAZEIiERAJAIiERCJgEgERCIgEgGRCIhEQCQCIjmfjVlzuJ1TsHbvAwAAAAAAAAAAAAAAwJHa3prfy+v7OTJrN28fL48Ps0Gbmwv7Sf5ujs1a+5/zYTbIZCqJgEgERCIgEgGRCIhEQCQCIhEQiYBIBEQiIBIBkQiIREAk23sP9IcO63Dz+fq8H37NDUQiIBIBkQiIREAkAiIREImASAREIiASAZEIiERAJAIiERCJgEgERCIgEgGRCIhEQCQCIhEQiYBIBEQiIBIBkQiIREAkAiLZ3HqX9YffIq3d1/sAAAAAAAAAAAAAAAAAAAAAR+0bJOgh1yNjXIEAAAAASUVORK5CYII=">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
      --bg-start: #f8fafc;
      --bg-end: #eef4ff;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --muted: #5f6b7c;
      --text: #111827;
      --green: #059669;
      --red: #dc2626;
      --amber: #d97706;
      --blue: #2563eb;
      --border: #d7e0ea;
      --card: #ffffff;
      --surface: rgba(255,255,255,.96);
      --surface-solid: #ffffff;
      --input-bg: #ffffff;
      --log-bg: #f8fafc;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      --radius-xl: 22px;
      --radius-lg: 18px;
      --radius-md: 14px;
      --radius-sm: 12px;
    }

    body[data-theme="light"] {
      --bg-start: #f8fafc;
      --bg-end: #e2e8f0;
      --bg: #f1f5f9;
      --panel: #ffffff;
      --muted: #475569;
      --text: #0f172a;
      --green: #059669;
      --red: #dc2626;
      --amber: #d97706;
      --blue: #2563eb;
      --border: #cbd5e1;
      --card: #ffffff;
      --surface: rgba(255,255,255,.94);
      --surface-solid: #ffffff;
      --input-bg: #ffffff;
      --log-bg: #f8fafc;
      --shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
    }
    body[data-theme="dark"] {
      --bg-start: #020617;
      --bg-end: #0f172a;
      --bg: #0f172a;
      --panel: #111827;
      --muted: #94a3b8;
      --text: #e5e7eb;
      --green: #10b981;
      --red: #ef4444;
      --amber: #f59e0b;
      --blue: #3b82f6;
      --border: #243041;
      --card: #111827;
      --surface: rgba(15, 23, 42, 0.92);
      --surface-solid: #111827;
      --input-bg: #0b1220;
      --log-bg: #020617;
      --shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      padding: 0;
      font-family: "Manrope", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(850px 380px at 10% -6%, rgba(37,99,235,.10), transparent 62%),
        radial-gradient(700px 320px at 92% -8%, rgba(5,150,105,.10), transparent 60%),
        linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
      min-height: 100vh;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(to bottom, rgba(255,255,255,0.015), transparent 30%);
      z-index: 0;
    }

    .wrap {
      width: 100%;
      max-width: 1660px;
      margin: 0 auto;
      padding: 18px 18px 26px;
      position: relative;
      z-index: 1;
    }

    .topbar {
      display: block;
      margin-bottom: 18px;
    }

    .hero-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(8px);
    }

    .hero-head {
      padding: 24px 24px 16px;
      border-bottom: 1px solid rgba(148,163,184,0.12);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
    }

    .hero-title-wrap h1 {
      margin: 0;
      font-size: 30px;
      line-height: 1.05;
      letter-spacing: 0.1px;
      font-weight: 800;
    }

    .hero-title-wrap p {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      word-break: break-word;
    }

    .hero-mini-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }

    .mini-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,.03);
      font-size: 12px;
      color: var(--muted);
    }

    .hero-body {
      padding: 18px 24px 24px;
    }

    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
    }

    @media (max-width: 1080px) {
      .hero-grid {
        grid-template-columns: 1fr;
      }
    }

    .subcard {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
      min-height: 100%;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.02);
    }

    .subcard-title {
      font-size: 14px;
      font-weight: 700;
      margin: 0 0 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .subcard-title .small-note {
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }

    .info-list {
      display: grid;
      gap: 10px;
      margin-bottom: 16px;
    }

    .info-item {
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(255,255,255,.02);
      padding: 12px 14px;
    }

    .info-item .label {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }

    .info-item .value {
      font-size: 14px;
      font-weight: 700;
      word-break: break-word;
    }

    .panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-xl);
      padding: 18px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }

    .panel h3 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
    }

    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }

    .panel-sub {
      color: var(--muted);
      font-size: 13px;
      margin-top: 6px;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 0 0 18px;
    }

    @media (max-width: 1180px) {
      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 640px) {
      .stats {
        grid-template-columns: 1fr;
      }
    }

    .stat {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px 16px;
      box-shadow: var(--shadow);
    }

    .stat .label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: .05em;
      font-weight: 700;
    }

    .stat .value {
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
      word-break: break-word;
    }

    .grid {
      display: block;
    }

    .sites-table-wrap {
      width: 100%;
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgba(255,255,255,.015);
    }

    .sites-table {
      min-width: 900px;
      table-layout: fixed;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    th, td {
      padding: 14px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }

    th {
      color: var(--muted);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: .08em;
      position: sticky;
      top: 0;
      background: var(--surface-solid);
      z-index: 1;
    }

    tbody tr:hover {
      background: rgba(59,130,246,.05);
    }

    tbody tr:last-child td {
      border-bottom: none;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      line-height: 1.2;
      white-space: nowrap;
    }

    .ok { background: rgba(16,185,129,.14); color: #047857; }
    .down { background: rgba(239,68,68,.14); color: #b91c1c; }
    .warn { background: rgba(245,158,11,.16); color: #92400e; }

    .loading {
      background: rgba(59,130,246,.16);
      color: #93c5fd;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .loading::before {
      content: "";
      width: 10px;
      height: 10px;
      border: 2px solid rgba(147,197,253,.35);
      border-top-color: #93c5fd;
      border-radius: 50%;
      animation: spin .8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .btn {
      border: none;
      padding: 10px 14px;
      border-radius: 12px;
      color: white;
      cursor: pointer;
      font-weight: 700;
      font-size: 13px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: transform .08s ease, filter .15s ease, opacity .15s ease, box-shadow .15s ease;
      box-shadow: 0 8px 18px rgba(0,0,0,.15);
    }

    .btn:hover {
      filter: brightness(1.06);
    }

    .btn:active {
      transform: translateY(1px);
    }

    .btn:disabled {
      opacity: .45;
      cursor: not-allowed;
      filter: grayscale(.2);
      box-shadow: none;
    }

    .btn-blue { background: var(--blue); }
    .btn-green { background: var(--green); }
    .btn-red { background: var(--red); }
    .btn-amber { background: var(--amber); color: #111827; }
    .btn-gray { background: #334155; }

    .action-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .top-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
      align-items: center;
    }

    .bench-switch {
      margin-top: 12px;
      max-width: 100%;
    }

    .bench-switch-label {
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: .06em;
      font-weight: 800;
    }

    .bench-switch-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
    }

    .bench-switch-row .btn {
      min-width: 140px;
      min-height: 44px;
    }

    .ssh-toggle-row {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      color: var(--text);
      font-weight: 700;
      margin-bottom: 8px;
    }

    .hidden {
      display: none !important;
    }

    .remote-list {
      margin-top: 8px;
      max-height: 170px;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--input-bg);
      padding: 10px 12px;
      font-family: Consolas, monospace;
      font-size: 12px;
      color: var(--text);
      white-space: pre-wrap;
    }

    .remote-select {
      margin-top: 8px;
    }

    .ssh-status {
      margin-top: 8px;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: rgba(59,130,246,.10);
      font-size: 12px;
      color: #bfdbfe;
      word-break: break-all;
    }

    .ssh-card {
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: var(--card);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.03);
    }

    .step-label {
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .05em;
      text-transform: uppercase;
      margin-bottom: 6px;
      font-weight: 800;
    }

    .site-actions {
      flex-wrap: nowrap;
      gap: 6px;
    }

    .site-actions .btn {
      padding: 8px 12px;
      min-width: 58px;
      font-size: 12px;
      border-radius: 10px;
      white-space: nowrap;
    }

    .actions-col {
      width: 195px;
    }

    .muted { color: var(--muted); }
    .small { font-size: 12px; }
    .mono { font-family: "JetBrains Mono", Consolas, monospace; }

    .logbox {
      background: var(--log-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      height: 360px;
      overflow: auto;
      white-space: pre-wrap;
      font-family: "JetBrains Mono", Consolas, monospace;
      font-size: 12.5px;
      line-height: 1.55;
    }
    .live-log-table-wrap {
      margin-bottom: 10px;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      background: var(--surface-solid);
    }
    .live-log-table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }
    .live-log-table th, .live-log-table td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
      vertical-align: middle;
    }
    .live-log-table th {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .05em;
      color: var(--muted);
      font-weight: 800;
    }
    .live-log-table tr:last-child td {
      border-bottom: none;
    }
    .live-log-head {
      margin-top: 8px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    .live-log-title {
      font-size: 13px;
      color: var(--muted);
      font-weight: 700;
    }

    .sites-tools {
      margin: 12px 0;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
    }

    .pager {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .pager-label {
      min-width: 92px;
      text-align: center;
      font-size: 12px;
      color: var(--muted);
      font-weight: 700;
    }

    input, select {
      width: 100%;
      background: var(--input-bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 11px 12px;
      outline: none;
      font: inherit;
      min-height: 44px;
    }

    input:focus, select:focus {
      border-color: rgba(59,130,246,.6);
      box-shadow: 0 0 0 3px rgba(59,130,246,.12);
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 140px auto;
      gap: 12px;
      align-items: end;
    }

    .form-run-btn {
      width: 100%;
      min-width: 120px;
    }

    @media (max-width: 860px) {
      .bench-switch-row,
      .form-grid {
        grid-template-columns: 1fr;
      }

      .sites-tools {
        grid-template-columns: 1fr;
      }

      .site-actions {
        flex-wrap: wrap;
      }
    }

    .login-wrap {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .login-card {
      width: 100%;
      max-width: 420px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 24px;
      box-shadow: 0 20px 50px rgba(0,0,0,.35);
    }

    .error {
      color: #fca5a5;
      margin-bottom: 12px;
      font-size: 14px;
    }

    .modal {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(2, 6, 23, 0.78);
      z-index: 9999;
      padding: 20px;
    }

    .modal.show { display: flex; }

    .modal-card {
      width: 100%;
      max-width: 430px;
      background: var(--surface-solid);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 18px 42px rgba(0,0,0,.4);
    }

    .modal-title {
      margin: 0 0 10px;
      font-size: 18px;
      font-weight: 800;
    }

    .modal-row {
      margin-top: 12px;
    }

    .modal-actions {
      margin-top: 16px;
      display: flex;
      gap: 10px;
      justify-content: flex-end;
      flex-wrap: wrap;
    }

    .url-list a {
      color: #93c5fd;
      text-decoration: none;
      display: block;
      margin-bottom: 4px;
      word-break: break-all;
      font-weight: 700;
    }

    .url-list a:hover {
      text-decoration: underline;
    }

    .toast-wrap {
      position: fixed;
      top: 18px;
      right: 18px;
      width: min(360px, calc(100vw - 30px));
      display: flex;
      flex-direction: column;
      gap: 10px;
      z-index: 11000;
      pointer-events: none;
    }

    .toast {
      border: 1px solid var(--border);
      border-left-width: 4px;
      border-radius: 14px;
      background: #ffffff;
      box-shadow: 0 10px 28px rgba(15, 23, 42, .12);
      padding: 12px 14px;
      font-size: 13px;
      line-height: 1.45;
      color: var(--text);
      transform: translateY(-6px);
      opacity: 0;
      transition: opacity .18s ease, transform .18s ease;
      pointer-events: auto;
    }

    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    .toast-success { border-left-color: #10b981; }
    .toast-error { border-left-color: #ef4444; }
    .toast-info { border-left-color: #3b82f6; }

    .floating-alert {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(2, 6, 23, 0.72);
      z-index: 12000;
      padding: 20px;
    }

    .floating-alert.show {
      display: flex;
    }

    .floating-alert-card {
      width: 100%;
      max-width: 420px;
      background: var(--surface-solid);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 20px 46px rgba(0,0,0,.45);
      padding: 16px;
    }

    .floating-alert-title {
      margin: 0 0 10px;
      font-size: 17px;
      font-weight: 800;
    }

    .floating-alert-text {
      font-size: 14px;
      line-height: 1.45;
      white-space: pre-wrap;
      color: var(--text);
      margin-bottom: 14px;
    }

    .floating-alert-actions {
      display: flex;
      justify-content: flex-end;
    }
  </style>
</head>
<body data-theme="light">
  {% if login %}
  <div class="login-wrap">
    <div class="login-card">
      <h2 style="margin-top:0;">{{ title }}</h2>
      <p class="muted">Enter panel password</p>
      {% if error %}<div class="error">{{ error }}</div>{% endif %}
      <form method="post" action="/login">
        <input type="password" name="password" placeholder="Password" required>
        <div style="height:12px"></div>
        <button class="btn btn-blue" type="submit">Login</button>
      </form>
    </div>
  </div>
  {% else %}
  <div class="wrap">
    <div class="topbar">
      <div class="hero-card">
        <div class="hero-head">
          <div class="hero-title-wrap">
            <h1>{{ title }}</h1>
            <p>Professional control panel for local and SSH benches with fast site actions and clean monitoring.</p>
            <div class="hero-mini-badges">
              <div class="mini-badge"><strong>Bench Path</strong> <span>{{ bench_path }}</span></div>
              <div class="mini-badge"><strong>Access Host</strong> <span id="accessHostText">{{ access_host }}</span></div>
              <div class="mini-badge"><strong>Bench Port</strong> <span>{{ common_port }}</span></div>
            </div>
          </div>
          <div class="action-row top-actions">
            <button class="btn btn-green" onclick="startBench()">Start Bench</button>
            <button class="btn btn-red" onclick="stopBench()">Stop Bench</button>
            <button class="btn btn-red" onclick="openForceStopModal()">Force Stop All Sites</button>
            <button id="themeToggleBtn" class="btn btn-gray" onclick="toggleTheme()">Theme</button>
            <button class="btn btn-gray" onclick="refreshAll()">Refresh</button>
            <a class="btn btn-amber" href="/logout">Logout</a>
          </div>
        </div>

        <div class="hero-body">
          <div class="hero-grid">
            <div id="localBenchControls" class="subcard">
              <div class="subcard-title">
                <span>Local Bench Configuration</span>
                <span class="small-note">Use localhost or your Wi-Fi / SSH system IP</span>
              </div>

              <div class="info-list">
                <div class="info-item">
                  <div class="label">Current Bench Path</div>
                  <div class="value mono">{{ bench_path }}</div>
                </div>
                <div class="info-item">
                  <div class="label">Current Access Host</div>
                  <div class="value" id="accessHostTextSecondary">{{ access_host }}</div>
                </div>
                <div class="info-item">
                  <div class="label">Common Bench Port</div>
                  <div class="value">{{ common_port }}</div>
                </div>
              </div>

              <div class="bench-switch">
                <div class="bench-switch-label">Set Access Host</div>
                <div class="bench-switch-row">
                  <input id="accessHostInput" type="text" value="{{ access_host }}" placeholder="127.0.0.1, localhost, 10.24.0.165, domain">
                  <button class="btn btn-blue" onclick="saveAccessHost()">Save Host</button>
                </div>
                <div style="height:8px"></div>
                <div class="bench-switch-row">
                  <div class="muted small">Leave empty to auto-detect system hostname</div>
                  <button class="btn btn-gray" onclick="resetAccessHost()">Use Auto Host</button>
                </div>
              </div>

              <div class="bench-switch">
                <div class="bench-switch-label">Switch Bench Path</div>
                <div class="bench-switch-row">
                  <input id="benchPathInput" type="text" value="{{ bench_path }}" placeholder="/home/solufy/frappe-bench">
                  <button class="btn btn-blue" onclick="requestBenchSwitch()">Switch Folder</button>
                </div>
                <div style="height:8px"></div>
                <div class="bench-switch-row">
                  <div class="muted small">Available local bench paths</div>
                  <button class="btn btn-gray" onclick="loadLocalBenchPaths()">Reload Paths</button>
                </div>
                <div id="localBenchList" class="remote-list muted">Loading local bench paths...</div>
              </div>
            </div>

            <div class="subcard ssh-card">
              <div class="subcard-title">
                <span>SSH Bench Browser</span>
                <span class="small-note">Connect and control another system</span>
              </div>

              <div class="ssh-toggle-row">
                <input id="sshEnableCheckbox" type="checkbox" style="width:auto;" onchange="toggleSshBrowse()">
                <label for="sshEnableCheckbox">Connect to SSH</label>
              </div>

              <div id="sshBrowseSection" class="hidden">
                <div class="ssh-status" id="sshStatusBox">Not connected</div>

                <div style="height:8px"></div>
                <div class="step-label">Step 1: Connect Host</div>
                <div class="bench-switch-row">
                  <input id="sshTargetInput" type="text" placeholder="user@host (example: solufy@10.24.0.165)">
                  <button class="btn btn-blue" onclick="fetchRemoteBenches(true)">Connect SSH</button>
                </div>

                <div style="height:8px"></div>
                <div class="step-label">Step 2: Bench Path or Base Path</div>
                <div class="bench-switch-row">
                  <input id="sshBasePathInput" type="text" value="{{ bench_path }}" placeholder="Remote frappe bench path or base path">
                  <button class="btn btn-gray" onclick="fetchRemoteBenches(false)">Refresh List</button>
                </div>

                <div class="remote-select">
                  <div class="step-label">Step 3: Select Folder</div>
                  <label class="muted small" for="sshBenchSelect">Remote Bench Folder</label>
                  <select id="sshBenchSelect" onchange="connectSelectedRemoteBench()">
                    <option value="">Select remote bench folder</option>
                  </select>
                </div>

                <div style="height:8px"></div>
                <div class="bench-switch-row">
                  <input id="sshPasswordInput" type="password" placeholder="SSH password (optional, for password login)">
                  <button class="btn btn-gray" onclick="connectSelectedRemoteBench()">Connect Selected Folder</button>
                </div>

                <div style="height:8px"></div>
                <div class="bench-switch-row">
                  <div class="muted small">Connected in SSH mode</div>
                  <button class="btn btn-red" onclick="disconnectSsh()">Disconnect SSH</button>
                </div>

                <div id="remoteBenchList" class="remote-list muted">No remote data yet.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="label">Bench Port Status</div>
        <div class="value" id="benchStatusText">-</div>
      </div>
      <div class="stat">
        <div class="label">Total Sites</div>
        <div class="value" id="siteCount">{{ sites|length }}</div>
      </div>
      <div class="stat">
        <div class="label">Custom Site Servers</div>
        <div class="value" id="customSiteCount">0</div>
      </div>
      <div class="stat">
        <div class="label">Last Refresh</div>
        <div class="value small" id="lastRefresh">-</div>
      </div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel-head">
          <div>
            <h3>Sites</h3>
            <div class="panel-sub">Open, run, and stop individual sites. Access links are shown using saved host or remote host.</div>
          </div>
        </div>
        <div class="sites-tools">
          <input id="siteSearchInput" type="text" placeholder="Search site name..." oninput="onSiteSearchInput()">
          <div class="pager">
            <button class="btn btn-gray" onclick="prevSitePage()">Prev</button>
            <span id="sitePageLabel" class="pager-label">Page 1 / 1</span>
            <button class="btn btn-gray" onclick="nextSitePage()">Next</button>
          </div>
        </div>

        <div class="sites-table-wrap">
          <table class="sites-table">
            <thead>
              <tr>
                <th>Site</th>
                <th>Site Path</th>
                <th>Status</th>
                <th>URL</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="sitesTableBody">
              {% for site in sites %}
              <tr>
                <td><strong>{{ site.name }}</strong></td>
                <td class="muted small mono">{{ site.site_path }}</td>
                <td><span class="badge warn">Checking...</span></td>
                <td class="muted small">{{ site.url_hint }}</td>
                <td class="actions-col">
                  <div class="action-row site-actions">
                    <button class="btn btn-blue" onclick="openSite('{{ site.name }}')">Open</button>
                    <button class="btn btn-green" onclick="openRunModal('{{ site.name }}', this)">Run</button>
                    <button class="btn btn-red" onclick="stopSpecificSite('{{ site.name }}')">Stop</button>
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head">
        <div>
          <h3>Logs</h3>
          <div class="panel-sub">Recent bench and site process output.</div>
        </div>
      </div>
      <div class="live-log-table-wrap">
        <table class="live-log-table">
          <thead>
            <tr>
              <th>Site</th>
              <th>Source</th>
              <th>Port</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="liveSiteLogTableBody">
            <tr><td colspan="4" class="muted">No live site servers.</td></tr>
          </tbody>
        </table>
      </div>
      <div class="live-log-head">
        <div id="selectedLiveLogTitle" class="live-log-title">Selected Site Log: none</div>
        <button class="btn btn-gray" onclick="refreshSelectedLiveSiteLog()">Refresh Live Site Log</button>
      </div>
      <div id="siteLiveLogBox" class="logbox">Select a running site from the table above to view live site log.</div>
      <div style="height:10px"></div>
      <div id="logBox" class="logbox">Loading logs...</div>
    </div>
  </div>

  <div id="runSiteModal" class="modal" onclick="handleModalBackdropClick(event)">
    <div class="modal-card">
      <h4 class="modal-title">Run Site</h4>
      <div class="muted small">Site</div>
      <div id="runModalSiteName" style="margin-top:4px;"><strong>-</strong></div>
      <div class="modal-row">
        <label class="muted small" for="runModalPort">Port (required)</label>
        <input id="runModalPort" type="number" min="1" max="65535" step="1" inputmode="numeric" required placeholder="Enter port e.g. 3434">
      </div>
      <div class="modal-actions">
        <button class="btn btn-gray" onclick="closeRunModal()">Cancel</button>
        <button id="runModalConfirmBtn" class="btn btn-green" onclick="confirmRunSite()">Run</button>
      </div>
    </div>
  </div>

  <div id="switchBenchModal" class="modal" onclick="handleModalBackdropClick(event)">
    <div class="modal-card">
      <h4 class="modal-title">Switch Bench Folder</h4>
      <div class="muted small">New Bench Path</div>
      <div id="switchModalBenchPath" style="margin-top:4px;" class="mono">-</div>
      <div class="modal-row muted small">
        Stop all old bench/site processes before switching, or keep them running and only switch this panel?
      </div>
      <div class="modal-actions">
        <button class="btn btn-gray" onclick="closeSwitchBenchModal()">Cancel</button>
        <button class="btn btn-blue" onclick="confirmSwitchBench(false)">Keep Running &amp; Switch</button>
        <button class="btn btn-red" onclick="confirmSwitchBench(true)">Stop All &amp; Switch</button>
      </div>
    </div>
  </div>

  <div id="forceStopModal" class="modal" onclick="handleModalBackdropClick(event)">
    <div class="modal-card">
      <h4 class="modal-title">Force Stop (sudo)</h4>
      <div class="modal-row muted small">
        This runs: <span class="mono">sudo pkill -f &quot;frappe&quot; &amp;&amp; sudo pkill redis-server</span>
      </div>
      <div class="modal-row">
        <label class="muted small" for="forceStopSudoPassword">Sudo Password</label>
        <input id="forceStopSudoPassword" type="password" placeholder="Enter sudo password" autocomplete="current-password">
      </div>
      <div class="modal-actions">
        <button class="btn btn-gray" onclick="closeForceStopModal()">Cancel</button>
        <button class="btn btn-red" onclick="confirmForceStopAllSites()">Force Stop</button>
      </div>
    </div>
  </div>

  <div id="toastWrap" class="toast-wrap"></div>

  <div id="floatingAlert" class="floating-alert">
    <div class="floating-alert-card">
      <h4 class="floating-alert-title">Notification</h4>
      <div id="floatingAlertText" class="floating-alert-text"></div>
      <div class="floating-alert-actions">
        <button class="btn btn-blue" onclick="closeFloatingAlert()">OK</button>
      </div>
    </div>
  </div>

  <script>
    async function api(path, method='GET', body=null) {
      const options = {
        method: method,
        headers: {'Content-Type': 'application/json'},
        credentials: 'same-origin'
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const res = await fetch(path, options);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Request failed');
      }

      return data;
    }

    const initialBenchPath = {{ bench_path|tojson }};
    const defaultRemoteBasePath = {{ bench_path|tojson }};
    let pendingSwitchBenchPath = '';
    let sshRemoteSession = null;
    let remoteSiteStatusByName = {};
    let siteRowsCache = [];
    let sitePage = 1;
    let siteSearch = '';
    let liveSiteEntries = [];
    let selectedLiveLogSite = '';
    let selectedLiveLogPort = null;
    let selectedLiveLogRemote = false;
    const SITE_PAGE_SIZE = 6;
    const SSH_STATE_KEY = 'bench_panel_ssh_state_v1';
    const THEME_STATE_KEY = 'bench_panel_theme_v1';

    function applyTheme(theme) {
      const selected = theme === 'light' ? 'light' : 'dark';
      document.body.setAttribute('data-theme', selected);
      const btn = document.getElementById('themeToggleBtn');
      if (btn) {
        btn.textContent = selected === 'light' ? 'Dark Mode' : 'Light Mode';
      }
      try {
        localStorage.setItem(THEME_STATE_KEY, selected);
      } catch (e) {
        console.error('Could not save theme', e);
      }
    }

    function toggleTheme() {
      const current = document.body.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      applyTheme(current === 'light' ? 'dark' : 'light');
    }
    window.toggleTheme = toggleTheme;

    function restoreTheme() {
      try {
        const saved = localStorage.getItem(THEME_STATE_KEY) || 'light';
        applyTheme(saved === 'dark' ? 'dark' : 'light');
      } catch (e) {
        applyTheme('light');
      }
    }

    function statusBadge(label, cls, extra='') {
      return `<span class="badge ${cls} ${extra}">${label}</span>`;
    }

    function jsEscape(text) {
      return String(text || '').replace(/'/g, "\\'");
    }

    function escapeHtml(value) {
      return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function onSiteSearchInput() {
      const input = document.getElementById('siteSearchInput');
      siteSearch = (input ? input.value : '').trim().toLowerCase();
      sitePage = 1;
      renderSiteRows();
    }
    window.onSiteSearchInput = onSiteSearchInput;

    function prevSitePage() {
      if (sitePage > 1) {
        sitePage -= 1;
        renderSiteRows();
      }
    }
    window.prevSitePage = prevSitePage;

    function nextSitePage() {
      const filteredCount = siteRowsCache.filter((r) => !siteSearch || r.name.toLowerCase().includes(siteSearch)).length;
      const totalPages = Math.max(1, Math.ceil(filteredCount / SITE_PAGE_SIZE));
      if (sitePage < totalPages) {
        sitePage += 1;
        renderSiteRows();
      }
    }
    window.nextSitePage = nextSitePage;

    function renderSiteRows() {
      const body = document.getElementById('sitesTableBody');
      const label = document.getElementById('sitePageLabel');
      if (!body) return;
      const filtered = siteRowsCache.filter((row) => !siteSearch || row.name.toLowerCase().includes(siteSearch));
      const totalPages = Math.max(1, Math.ceil(filtered.length / SITE_PAGE_SIZE));
      if (sitePage > totalPages) sitePage = totalPages;
      const start = (sitePage - 1) * SITE_PAGE_SIZE;
      const pageRows = filtered.slice(start, start + SITE_PAGE_SIZE);
      body.innerHTML = pageRows.map((row) => row.html).join('');
      if (label) {
        label.textContent = `Page ${sitePage} / ${totalPages}`;
      }
    }

    function renderLiveSiteLogTable(entries) {
      const body = document.getElementById('liveSiteLogTableBody');
      if (!body) return;
      const rows = entries || [];
      if (!rows.length) {
        body.innerHTML = '<tr><td colspan="4" class="muted">No live site servers.</td></tr>';
        return;
      }
      body.innerHTML = rows.map((r) => {
        const siteArg = encodeURIComponent(r.site || '');
        const portArg = Number.isInteger(Number(r.port)) ? Number(r.port) : null;
        const remoteArg = r.remote ? 'true' : 'false';
        return `<tr>
          <td><strong>${escapeHtml(r.site || '')}</strong></td>
          <td>${escapeHtml(r.source || '-')}</td>
          <td>${r.port ? String(r.port) : '-'}</td>
          <td><button class="btn btn-blue" onclick="openLiveSiteLog(decodeURIComponent('${siteArg}'), ${portArg === null ? 'null' : portArg}, ${remoteArg})">View Log</button></td>
        </tr>`;
      }).join('');
    }

    async function openLiveSiteLog(site, port=null, remote=false) {
      selectedLiveLogSite = String(site || '').trim();
      selectedLiveLogPort = port === null ? null : Number(port);
      selectedLiveLogRemote = Boolean(remote);
      const title = document.getElementById('selectedLiveLogTitle');
      if (title) {
        const src = selectedLiveLogRemote ? 'SSH' : 'Local';
        const portLabel = selectedLiveLogPort ? `:${selectedLiveLogPort}` : '';
        title.textContent = `Selected Site Log: ${selectedLiveLogSite} (${src}${portLabel})`;
      }
      await refreshSelectedLiveSiteLog(false);
    }
    window.openLiveSiteLog = openLiveSiteLog;

    async function refreshSelectedLiveSiteLog(silent=true) {
      const box = document.getElementById('siteLiveLogBox');
      if (!box) return;
      if (!selectedLiveLogSite) {
        box.textContent = 'Select a running site from the table above to view live site log.';
        return;
      }
      try {
        let data;
        if (selectedLiveLogRemote) {
          if (!sshRemoteSession) {
            box.textContent = 'SSH session not connected.';
            return;
          }
          data = await api('/api/ssh/site/live-log', 'POST', {
            ...sshRemoteSession,
            site: selectedLiveLogSite,
            port: selectedLiveLogPort,
            lines: 180,
          });
        } else {
          data = await api(`/api/site/live-log?site=${encodeURIComponent(selectedLiveLogSite)}&lines=180`);
        }
        box.textContent = (data.logs || []).join('\n') || 'No log lines yet.';
        box.scrollTop = box.scrollHeight;
      } catch (e) {
        box.textContent = `Could not load live site log: ${e.message || 'unknown error'}`;
        if (!silent) showToast(e.message || 'Live log failed', 'error');
      }
    }
    window.refreshSelectedLiveSiteLog = refreshSelectedLiveSiteLog;

    function showToast(message, type='info') {
      const wrap = document.getElementById('toastWrap');
      if (!wrap) return;

      const toast = document.createElement('div');
      const safeType = ['success', 'error', 'info'].includes(type) ? type : 'info';
      toast.className = `toast toast-${safeType}`;
      toast.textContent = message || 'Done';
      wrap.appendChild(toast);

      requestAnimationFrame(() => toast.classList.add('show'));

      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 220);
      }, 3200);
    }

    function showFloatingAlert(message) {
      const modal = document.getElementById('floatingAlert');
      const text = document.getElementById('floatingAlertText');
      if (!modal || !text) return;
      text.textContent = message || '';
      modal.classList.add('show');
    }

    function closeFloatingAlert() {
      const modal = document.getElementById('floatingAlert');
      if (!modal) return;
      modal.classList.remove('show');
    }

    window.alert = function(message) {
      showFloatingAlert(message);
    };

    function requestBenchSwitch() {
      const input = document.getElementById('benchPathInput');
      if (!input) return;
      const newPath = input.value.trim();
      if (!newPath) {
        showToast('Bench path is required', 'error');
        return;
      }
      if (newPath === initialBenchPath) {
        showToast('Already using this bench folder', 'info');
        return;
      }
      pendingSwitchBenchPath = newPath;
      document.getElementById('switchModalBenchPath').textContent = newPath;
      document.getElementById('switchBenchModal').classList.add('show');
    }

    function useBenchPath(path) {
      const input = document.getElementById('benchPathInput');
      if (input) input.value = path || '';
      showToast('Path selected. Click "Switch Folder" to apply.', 'info');
    }
    window.useBenchPath = useBenchPath;

    async function loadLocalBenchPaths() {
      const box = document.getElementById('localBenchList');
      if (!box) return;
      box.textContent = 'Loading local bench paths...';
      try {
        const data = await api('/api/bench/paths');
        const paths = data.paths || [];
        if (!paths.length) {
          box.textContent = 'No bench paths found.';
          return;
        }
        const items = paths.map((p) => {
          const safe = escapeHtml(p);
          const encoded = encodeURIComponent(p);
          return `<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:8px;"><div class="path-text">${safe}</div><button class="btn btn-blue" onclick="useBenchPath(decodeURIComponent('${encoded}'))">Use</button></div>`;
        });
        box.innerHTML = items.join('');
      } catch (e) {
        box.textContent = `Failed to load bench paths: ${e.message || 'unknown error'}`;
      }
    }
    window.loadLocalBenchPaths = loadLocalBenchPaths;

    function closeSwitchBenchModal() {
      document.getElementById('switchBenchModal').classList.remove('show');
      pendingSwitchBenchPath = '';
    }

    async function confirmSwitchBench(stopExisting) {
      if (!pendingSwitchBenchPath) {
        closeSwitchBenchModal();
        return;
      }

      const targetPath = pendingSwitchBenchPath;
      closeSwitchBenchModal();

      try {
        const result = await api('/api/bench/switch', 'POST', {
          bench_path: targetPath,
          stop_existing: Boolean(stopExisting),
        });
        showToast(result.message || 'Bench folder switched', 'success');
        setTimeout(() => window.location.reload(), 350);
      } catch (e) {
        showToast(e.message || 'Failed to switch bench folder', 'error');
      }
    }

    async function saveAccessHost() {
      const input = document.getElementById('accessHostInput');
      if (!input) return;
      const host = input.value.trim();
      if (!host) {
        showToast('Access host is required. Use "Use Auto Host" to reset.', 'error');
        return;
      }
      try {
        const result = await api('/api/access-host', 'POST', {host});
        showToast(result.message || 'Access host updated', 'success');
        await refreshAll();
      } catch (e) {
        showToast(e.message || 'Failed to update access host', 'error');
      }
    }

    async function resetAccessHost() {
      try {
        const result = await api('/api/access-host', 'POST', {host: ''});
        showToast(result.message || 'Access host reset to auto', 'success');
        await refreshAll();
      } catch (e) {
        showToast(e.message || 'Failed to reset access host', 'error');
      }
    }

    function setSshStatus(message) {
      const box = document.getElementById('sshStatusBox');
      if (!box) return;
      box.textContent = message || 'Not connected';
    }

    async function fetchRemoteBenches(autoConnect=true) {
      const enabled = document.getElementById('sshEnableCheckbox');
      if (!enabled || !enabled.checked) {
        showToast('Enable "Connect to SSH" first', 'info');
        return;
      }
      const targetInput = document.getElementById('sshTargetInput');
      const baseInput = document.getElementById('sshBasePathInput');
      const passwordInput = document.getElementById('sshPasswordInput');
      const listBox = document.getElementById('remoteBenchList');
      const select = document.getElementById('sshBenchSelect');
      if (!targetInput || !baseInput || !passwordInput || !listBox || !select) return;

      const sshTarget = targetInput.value.trim();
      const basePath = baseInput.value.trim();
      const sshPassword = passwordInput.value;
      if (!sshTarget) {
        showToast('SSH target is required (example: user@host)', 'error');
        return;
      }

      listBox.textContent = 'Connecting over SSH...';
      setSshStatus(`Connecting to ${sshTarget}...`);
      try {
        const result = await api('/api/ssh/benches', 'POST', {
          ssh_target: sshTarget,
          base_path: basePath || defaultRemoteBasePath,
          ssh_password: sshPassword || '',
        });
        const benches = result.benches || [];
        select.innerHTML = '<option value="">Select remote bench folder</option>';
        for (const bench of benches) {
          const opt = document.createElement('option');
          opt.value = bench;
          opt.textContent = bench;
          select.appendChild(opt);
        }
        if (!benches.length) {
          listBox.textContent = 'No bench folders found on remote host.';
          sshRemoteSession = null;
          persistSshState();
          setSshStatus(`Connected to ${sshTarget}, but no bench folders found.`);
        } else {
          listBox.textContent = benches.join('\\n');
          select.value = benches[0];
          persistSshState();
          setSshStatus(`Host connected: ${sshTarget}. ${benches.length} folder(s) found.`);
          if (autoConnect) {
            await connectSelectedRemoteBench();
          } else {
            showToast(`Found ${benches.length} folder(s). Select folder to load sites.`, 'info');
          }
        }
        if (!autoConnect) {
          showToast(result.message || `Found ${benches.length} bench folder(s)`, 'success');
        }
      } catch (e) {
        listBox.textContent = `Failed: ${e.message || 'unknown error'}`;
        sshRemoteSession = null;
        persistSshState();
        setSshStatus(`SSH failed: ${e.message || 'unknown error'}`);
        if (select) {
          select.innerHTML = '<option value="">Select remote bench folder</option>';
        }
        showToast(e.message || 'SSH browse failed', 'error');
      }
    }
    window.fetchRemoteBenches = fetchRemoteBenches;

    async function connectSelectedRemoteBench() {
      const enabled = document.getElementById('sshEnableCheckbox');
      const targetInput = document.getElementById('sshTargetInput');
      const passwordInput = document.getElementById('sshPasswordInput');
      const select = document.getElementById('sshBenchSelect');
      if (!enabled || !enabled.checked || !targetInput || !passwordInput || !select) return;
      const sshTarget = targetInput.value.trim();
      const sshPassword = passwordInput.value;
      const selectedBench = (select.value || '').trim();
      if (!sshTarget) {
        showToast('SSH target is required', 'error');
        return;
      }
      if (!selectedBench) {
        showToast('Select a remote bench folder first', 'error');
        setSshStatus('Select a remote bench folder to load sites.');
        return;
      }
      sshRemoteSession = {
        ssh_target: sshTarget,
        bench_path: selectedBench,
        ssh_password: sshPassword || '',
      };
      persistSshState();
      try {
        await refreshRemoteStatus();
        setSshStatus(`Connected: ${sshTarget} -> ${selectedBench}`);
        showToast(`Connected to ${selectedBench}`, 'success');
      } catch (e) {
        sshRemoteSession = null;
        persistSshState();
        setSshStatus(`Folder connect failed: ${e.message || 'unknown error'}`);
        showToast(e.message || 'Failed to connect selected remote bench', 'error');
      }
    }
    window.connectSelectedRemoteBench = connectSelectedRemoteBench;

    function disconnectSsh() {
      const enabled = document.getElementById('sshEnableCheckbox');
      const targetInput = document.getElementById('sshTargetInput');
      const baseInput = document.getElementById('sshBasePathInput');
      const passwordInput = document.getElementById('sshPasswordInput');
      const select = document.getElementById('sshBenchSelect');
      const listBox = document.getElementById('remoteBenchList');

      sshRemoteSession = null;
      remoteSiteStatusByName = {};
      if (enabled) enabled.checked = false;
      if (targetInput) targetInput.value = '';
      if (baseInput) baseInput.value = '';
      if (passwordInput) passwordInput.value = '';
      if (select) select.innerHTML = '<option value="">Select remote bench folder</option>';
      if (listBox) listBox.textContent = 'No remote data yet.';
      setSshStatus('Not connected');
      try {
        localStorage.removeItem(SSH_STATE_KEY);
      } catch (e) {
        console.error('Could not clear SSH state', e);
      }
      toggleSshBrowse(false);
      refreshAll();
      showToast('SSH disconnected', 'info');
    }
    window.disconnectSsh = disconnectSsh;

    function persistSshState() {
      const enabled = document.getElementById('sshEnableCheckbox');
      const targetInput = document.getElementById('sshTargetInput');
      const baseInput = document.getElementById('sshBasePathInput');
      const passwordInput = document.getElementById('sshPasswordInput');
      const select = document.getElementById('sshBenchSelect');
      if (!enabled || !targetInput || !baseInput || !passwordInput || !select) return;
      const payload = {
        enabled: Boolean(enabled.checked),
        ssh_target: targetInput.value || '',
        base_path: baseInput.value || '',
        selected_bench: select.value || '',
        ssh_password: passwordInput.value || '',
      };
      try {
        localStorage.setItem(SSH_STATE_KEY, JSON.stringify(payload));
      } catch (e) {
        console.error('Could not persist SSH state', e);
      }
    }

    async function restoreSshState() {
      try {
        const raw = localStorage.getItem(SSH_STATE_KEY);
        if (!raw) return;
        const state = JSON.parse(raw);
        const enabled = document.getElementById('sshEnableCheckbox');
        const targetInput = document.getElementById('sshTargetInput');
        const baseInput = document.getElementById('sshBasePathInput');
        const passwordInput = document.getElementById('sshPasswordInput');
        const select = document.getElementById('sshBenchSelect');
        if (!enabled || !targetInput || !baseInput || !passwordInput || !select) return;

        enabled.checked = Boolean(state.enabled);
        targetInput.value = state.ssh_target || '';
        baseInput.value = state.base_path || '';
        passwordInput.value = state.ssh_password || '';
        toggleSshBrowse(false);
        if (!enabled.checked || !targetInput.value.trim()) {
          setSshStatus('Not connected');
          return;
        }

        await fetchRemoteBenches();
        if (state.selected_bench) {
          select.value = state.selected_bench;
        }
        if (select.value) {
          await connectSelectedRemoteBench();
        } else {
          setSshStatus(`Host connected: ${targetInput.value.trim()}. Select folder to load sites.`);
        }
      } catch (e) {
        console.error('Could not restore SSH state', e);
      }
    }

    function toggleSshBrowse(shouldPersist=true) {
      const checkbox = document.getElementById('sshEnableCheckbox');
      const section = document.getElementById('sshBrowseSection');
      if (!checkbox || !section) return;
      if (checkbox.checked) {
        section.classList.remove('hidden');
        if (!sshRemoteSession) setSshStatus('SSH mode enabled. Connect host and select folder.');
        if (shouldPersist) persistSshState();
      } else {
        section.classList.add('hidden');
        sshRemoteSession = null;
        setSshStatus('Not connected');
        if (shouldPersist) persistSshState();
        refreshAll();
      }
    }
    window.toggleSshBrowse = toggleSshBrowse;

    function buildUrlHints(protocol, accessHost, port) {
      const hosts = ['127.0.0.1'];
      if (accessHost && accessHost !== '127.0.0.1' && accessHost !== 'localhost') {
        hosts.push(accessHost);
      }
      const links = hosts.map((host) => {
        const url = `${protocol}://${host}:${port}`;
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });
      return `<div class="url-list">${links.join('')}</div>`;
    }

    function renderRemoteSites(remoteSites) {
      const rows = [];
      remoteSiteStatusByName = {};
      const liveEntries = [];
      const sortedRemoteSites = [...(remoteSites || [])].sort((a, b) => {
        const rank = (s) => {
          if (s === 'running_custom') return 0;
          if (s === 'running_common') return 1;
          if (s === 'running_common_unknown') return 2;
          return 3;
        };
        const aRank = rank(a.status || 'stopped');
        const bRank = rank(b.status || 'stopped');
        if (aRank !== bRank) return aRank - bRank;
        return String(a.name || '').localeCompare(String(b.name || ''));
      });
      for (const site of sortedRemoteSites) {
        const status = site.status || 'stopped';
        let statusHtml = statusBadge('Stopped', 'down');
        let hint = '-';
        let openEnabled = false;
        if (status === 'running_custom' && site.running_port) {
          statusHtml = statusBadge(`Running on remote custom ${site.running_port}`, 'ok');
          hint = site.open_url || '-';
          openEnabled = Boolean(site.open_url);
          liveEntries.push({site: site.name, source: 'SSH custom', port: site.running_port, remote: true});
        } else if (status === 'running_common') {
          statusHtml = statusBadge('Served via remote bench', 'warn');
          hint = site.open_url || '-';
          openEnabled = Boolean(site.open_url);
          liveEntries.push({site: site.name, source: 'SSH common', port: site.running_port || 8000, remote: true});
        } else if (status === 'running_common_unknown') {
          statusHtml = statusBadge('Bench running on 8000 (default unknown)', 'warn');
          hint = site.open_url || '-';
          openEnabled = Boolean(site.open_url);
        }
        remoteSiteStatusByName[site.name] = site;
        const rowHtml = `
          <td><strong>${site.name}</strong></td>
          <td class="muted small mono">${site.site_path}</td>
          <td>${statusHtml}</td>
          <td class="muted small">${hint}</td>
          <td class="actions-col">
            <div class="action-row site-actions">
              <button class="btn btn-blue" onclick="openRemoteSite('${jsEscape(site.name)}')" ${openEnabled ? '' : 'disabled'}>Open</button>
              <button class="btn btn-green" onclick="openRunModal('${jsEscape(site.name)}', this)">Run</button>
              <button class="btn btn-red" onclick="stopSpecificSite('${jsEscape(site.name)}')">Stop</button>
            </div>
          </td>
        `;
        rows.push({name: site.name, html: `<tr>${rowHtml}</tr>`});
      }
      siteRowsCache = rows;
      renderSiteRows();
      liveSiteEntries = liveEntries;
      renderLiveSiteLogTable(liveSiteEntries);
    }

    function openRemoteSite(site) {
      const row = remoteSiteStatusByName[site];
      if (!row || !row.open_url) {
        showToast(`Site ${site} is not reachable on remote bench`, 'info');
        return;
      }
      window.open(row.open_url, '_blank');
    }

    async function refreshRemoteStatus() {
      if (!sshRemoteSession) return;
      const data = await api('/api/ssh/sites', 'POST', sshRemoteSession);
      const sites = data.sites || [];
      const benchText = data.common_running
        ? (data.default_site
          ? `SSH Running on ${data.common_port} (${data.default_site})`
          : `SSH Running on ${data.common_port} (default site unknown)`)
        : 'SSH Stopped';
      document.getElementById('benchStatusText').textContent = benchText;
      const customCount = sites.filter(x => x.status === 'running_custom').length;
      document.getElementById('customSiteCount').textContent = String(customCount);
      document.getElementById('siteCount').textContent = String(sites.length);
      document.getElementById('lastRefresh').textContent = new Date().toLocaleString();
      renderRemoteSites(sites);
      const listBox = document.getElementById('remoteBenchList');
      if (listBox && sshRemoteSession.bench_path) {
        listBox.textContent = sshRemoteSession.bench_path;
      }
    }

    async function refreshStatus() {
      if (sshRemoteSession) {
        await refreshRemoteStatus();
        return;
      }
      const data = await api('/api/status');

      document.getElementById('benchStatusText').textContent =
        data.common_port_running ? `Running on ${data.common_port}` : 'Stopped';

      document.getElementById('customSiteCount').textContent = data.running_site_servers.length;
      document.getElementById('lastRefresh').textContent = new Date().toLocaleString();
      document.getElementById('siteCount').textContent = data.sites.length;
      const hostText = document.getElementById('accessHostText');
      if (hostText) hostText.textContent = data.access_host || '-';
      const hostTextSecondary = document.getElementById('accessHostTextSecondary');
      if (hostTextSecondary) hostTextSecondary.textContent = data.access_host || '-';
      const hostInput = document.getElementById('accessHostInput');
      if (hostInput && document.activeElement !== hostInput) {
        hostInput.value = data.access_host || '';
      }

      const rows = [];
      const liveEntries = [];
      const customBySite = {};
      for (const server of (data.running_site_servers || [])) {
        customBySite[server.site] = server;
        liveEntries.push({site: server.site, source: 'Local custom', port: server.port, remote: false});
      }
      if (data.common_port_running && data.common_port_site) {
        liveEntries.push({site: data.common_port_site, source: 'Local common', port: data.common_port, remote: false});
      }
      const sortedSites = [...(data.sites || [])].sort((a, b) => {
        const aCustom = Boolean(customBySite[a.name]);
        const bCustom = Boolean(customBySite[b.name]);
        const aCommon = Boolean(data.common_port_running && data.common_port_site === a.name);
        const bCommon = Boolean(data.common_port_running && data.common_port_site === b.name);
        const aPending = pendingRunSites.has(a.name);
        const bPending = pendingRunSites.has(b.name);
        const aRank = aCustom ? 0 : (aCommon ? 1 : (aPending ? 2 : 3));
        const bRank = bCustom ? 0 : (bCommon ? 1 : (bPending ? 2 : 3));
        if (aRank !== bRank) return aRank - bRank;
        return String(a.name || '').localeCompare(String(b.name || ''));
      });

      for (const site of sortedSites) {
        const custom = customBySite[site.name];
        const commonMatch = data.common_port_running && data.common_port_site === site.name;

        let statusHtml = statusBadge('Stopped', 'down');
        let hint = '-';
        let openEnabled = false;

        if (pendingRunSites.has(site.name)) {
          statusHtml = statusBadge('Starting...', 'loading', 'loading');
          hint = 'Starting site...';
        }

        if (custom) {
          statusHtml = statusBadge(`Running on custom port ${custom.port}`, 'ok');
          hint = buildUrlHints(data.protocol, data.access_host, custom.port);
          openEnabled = true;
          pendingRunSites.delete(site.name);
        } else if (commonMatch) {
          statusHtml = statusBadge(`Served via bench on ${data.common_port}`, 'warn');
          hint = buildUrlHints(data.protocol, data.access_host, data.common_port);
          openEnabled = true;
          pendingRunSites.delete(site.name);
        }

        const rowHtml = `
          <td><strong>${site.name}</strong></td>
          <td class="muted small mono">${site.site_path}</td>
          <td>${statusHtml}</td>
          <td class="muted small">${hint}</td>
          <td class="actions-col">
            <div class="action-row site-actions">
              <button class="btn btn-blue" onclick="openSite('${jsEscape(site.name)}')" ${openEnabled ? '' : 'disabled'}>Open</button>
              <button class="btn btn-green" onclick="openRunModal('${jsEscape(site.name)}', this)">Run</button>
              <button class="btn btn-red" onclick="stopSpecificSite('${jsEscape(site.name)}')">Stop</button>
            </div>
          </td>
        `;
        rows.push({name: site.name, html: `<tr>${rowHtml}</tr>`});
      }
      siteRowsCache = rows;
      renderSiteRows();
      liveSiteEntries = liveEntries;
      renderLiveSiteLogTable(liveSiteEntries);
    }

    async function refreshLogs() {
      const data = await api('/api/logs');
      const box = document.getElementById('logBox');
      box.textContent = (data.logs || []).join('\\n');
      box.scrollTop = box.scrollHeight;
    }

    async function refreshAll() {
      try {
        await refreshStatus();
      } catch (e) {
        console.error('Status refresh failed:', e);
      }

      try {
        await refreshLogs();
      } catch (e) {
        console.error('Logs refresh failed:', e);
        const box = document.getElementById('logBox');
        if (box) {
          box.textContent = 'Could not load logs: ' + e.message;
        }
      }
      if (selectedLiveLogSite) {
        await refreshSelectedLiveSiteLog(true);
      }
    }

    async function startBench() {
      try {
        const result = sshRemoteSession
          ? await api('/api/ssh/bench/start', 'POST', sshRemoteSession)
          : await api('/api/bench/start', 'POST');
        showToast(result.message, 'success');
        await refreshAll();
      } catch (e) {
        showToast(e.message || 'Failed to start bench', 'error');
      }
    }

    async function stopBench() {
      try {
        const result = sshRemoteSession
          ? await api('/api/ssh/bench/stop', 'POST', sshRemoteSession)
          : await api('/api/bench/stop', 'POST');
        showToast(result.message, 'success');
        await refreshAll();
      } catch (e) {
        showToast(e.message || 'Failed to stop bench', 'error');
      }
    }

    function openForceStopModal() {
      const label = document.querySelector('label[for="forceStopSudoPassword"]');
      const input = document.getElementById('forceStopSudoPassword');
      if (label) {
        label.textContent = sshRemoteSession ? 'Remote Sudo Password (optional)' : 'Sudo Password';
      }
      if (input) {
        input.value = '';
        input.placeholder = sshRemoteSession
          ? 'Leave empty to use SSH password'
          : 'Enter sudo password';
      }
      document.getElementById('forceStopModal').classList.add('show');
      if (input) {
        input.focus();
      }
    }

    function closeForceStopModal() {
      document.getElementById('forceStopModal').classList.remove('show');
      const input = document.getElementById('forceStopSudoPassword');
      if (input) {
        input.value = '';
      }
    }

    async function confirmForceStopAllSites() {
      const input = document.getElementById('forceStopSudoPassword');
      const sudoPassword = input ? input.value : '';
      if (!sshRemoteSession && !sudoPassword) {
        showToast('Sudo password is required', 'error');
        return;
      }

      try {
        const result = sshRemoteSession
          ? await api('/api/ssh/force-stop-all', 'POST', {
              ...sshRemoteSession,
              sudo_password: sudoPassword || (sshRemoteSession.ssh_password || ''),
            })
          : await api('/api/site/force-stop-all', 'POST', {
              sudo_password: sudoPassword
            });
        closeForceStopModal();
        showToast(result.message || 'All site servers force-stopped', 'success');
        await refreshAll();
      } catch (e) {
        showToast(e.message || 'Failed to force-stop all sites', 'error');
      }
    }

    function openSite(site) {
      if (sshRemoteSession) {
        openRemoteSite(site);
        return;
      }
      window.open(`/open-site/${encodeURIComponent(site)}`, '_blank');
    }

    let runRequestInProgress = false;
    let pendingRunSite = '';
    let pendingRunButton = null;
    const pendingRunSites = new Set();

    function openRunModal(site, buttonEl=null) {
      if (runRequestInProgress) return;
      pendingRunSite = site;
      pendingRunButton = buttonEl;
      document.getElementById('runModalSiteName').innerHTML = `<strong>${site}</strong>`;
      const portInput = document.getElementById('runModalPort');
      portInput.value = '';
      document.getElementById('runSiteModal').classList.add('show');
      portInput.focus();
    }

    function closeRunModal() {
      document.getElementById('runSiteModal').classList.remove('show');
      pendingRunSite = '';
      pendingRunButton = null;
    }

    function handleModalBackdropClick(event) {
      if (event.target && event.target.id === 'runSiteModal') {
        closeRunModal();
      } else if (event.target && event.target.id === 'switchBenchModal') {
        closeSwitchBenchModal();
      } else if (event.target && event.target.id === 'forceStopModal') {
        closeForceStopModal();
      }
    }

    async function confirmRunSite() {
      if (!pendingRunSite) return;
      if (runRequestInProgress) return;
      const portValue = document.getElementById('runModalPort').value.trim();
      if (!/^[0-9]+$/.test(portValue)) {
        showToast('Port is required and must contain numbers only', 'error');
        return;
      }

      const numericPort = Number(portValue);
      if (!Number.isInteger(numericPort) || numericPort < 1 || numericPort > 65535) {
        showToast('Port must be between 1 and 65535', 'error');
        return;
      }

      runRequestInProgress = true;
      const confirmBtn = document.getElementById('runModalConfirmBtn');
      const siteToRun = pendingRunSite;
      const buttonEl = pendingRunButton;
      const payload = {site: siteToRun, port: numericPort};

      confirmBtn.disabled = true;
      if (buttonEl) buttonEl.disabled = true;
      closeRunModal();
      pendingRunSites.add(siteToRun);
      await refreshStatus();

      try {
        const result = sshRemoteSession
          ? await api('/api/ssh/site/run', 'POST', {
              ...sshRemoteSession,
              ...payload,
            })
          : await api('/api/site/run', 'POST', payload);
        showToast(result.message, 'success');
        await refreshAll();
      } catch (e) {
        pendingRunSites.delete(siteToRun);
        showToast(e.message || `Failed to run ${siteToRun}`, 'error');
        await refreshStatus();
      } finally {
        runRequestInProgress = false;
        confirmBtn.disabled = false;
        if (buttonEl) buttonEl.disabled = false;
      }
    }

    async function stopSpecificSite(site) {
      try {
        const result = sshRemoteSession
          ? await api('/api/ssh/site/stop', 'POST', {
              ...sshRemoteSession,
              site,
            })
          : await api('/api/site/stop', 'POST', {site});
        showToast(result.message, 'success');
        await refreshAll();
      } catch (e) {
        showToast(e.message || `Failed to stop ${site}`, 'error');
      }
    }

    restoreTheme();
    toggleSshBrowse(false);
    restoreSshState().finally(() => {
      loadLocalBenchPaths();
      refreshAll();
    });
    setInterval(refreshAll, 5000);
  </script>
  {% endif %}
</body>
</html>
"""


@dataclass
class SiteServer:
    site: str
    port: int
    pid: int
    started_at: str
    command: List[str]
    log_file: str


class BenchManager:
    def __init__(self, bench_path: str):
        self.bench_path = Path(bench_path).resolve()
        self.sites_path = self.bench_path / "sites"
        self.logs: List[str] = []
        self.bench_process: Optional[subprocess.Popen] = None
        self.site_processes: Dict[str, subprocess.Popen] = {}
        self.site_servers: Dict[str, SiteServer] = {}
        self.lock = threading.RLock()
        self.runtime_dir = self.bench_path / ".bench_panel_runtime"
        self.runtime_dir.mkdir(exist_ok=True)
        self.state_file = self.runtime_dir / "site_servers.json"
        self.bench_log = self.runtime_dir / "bench.log"
        self.access_host_file = self.runtime_dir / "access_host.txt"
        self.access_host_override = self._load_access_host_override()
        self._restore_state()

    def log(self, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {message}"
        with self.lock:
            self.logs.append(line)
            self.logs = self.logs[-500:]

    def _load_access_host_override(self) -> Optional[str]:
        try:
            if self.access_host_file.exists():
                saved = self.access_host_file.read_text(errors="ignore").strip()
                return saved or None
        except Exception:
            return None
        return None

    def _save_access_host_override(self) -> None:
        try:
            if self.access_host_override:
                self.access_host_file.write_text(self.access_host_override)
            elif self.access_host_file.exists():
                self.access_host_file.unlink()
        except Exception:
            pass

    def list_local_bench_paths(self) -> Dict[str, object]:
        roots: List[Path] = []
        home = Path.home()
        roots.append(home)
        roots.append(self.bench_path.parent)
        unique_roots: List[Path] = []
        seen_roots = set()
        for root in roots:
            resolved = root.resolve()
            if str(resolved) not in seen_roots and resolved.exists():
                seen_roots.add(str(resolved))
                unique_roots.append(resolved)

        found: set[str] = set()
        for root in unique_roots:
            try:
                proc = subprocess.run(
                    ["find", str(root), "-maxdepth", "5", "-type", "d", "-name", "sites"],
                    cwd=str(self.bench_path),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=25,
                )
            except Exception:
                continue

            if proc.returncode not in (0, 1):
                continue

            for line in (proc.stdout or "").splitlines():
                sites_dir = Path(line.strip())
                if not sites_dir.name == "sites":
                    continue
                bench_dir = sites_dir.parent
                if bench_dir.exists():
                    found.add(str(bench_dir))

        current = str(self.bench_path)
        sorted_paths = sorted(found)
        if current in sorted_paths:
            sorted_paths.remove(current)
            sorted_paths.insert(0, current)
        elif current:
            sorted_paths.insert(0, current)

        return {"paths": sorted_paths}

    def set_access_host(self, host: str) -> Dict[str, str]:
        value = (host or "").strip()
        if value:
            if "://" in value or "/" in value or value.startswith("."):
                raise ValueError("Access host must be a hostname/IP only, without protocol or path.")
            if not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
                raise ValueError("Access host contains invalid characters.")
            self.access_host_override = value
            self._save_access_host_override()
            return {"message": f"Access host set to {value}", "access_host": value}

        self.access_host_override = None
        self._save_access_host_override()
        auto_host = self.detect_access_host()
        return {"message": f"Access host reset to auto ({auto_host})", "access_host": auto_host}

    def list_remote_bench_folders(
        self, ssh_target: str, base_path: str = "~", ssh_password: str = ""
    ) -> Dict[str, object]:
        target = (ssh_target or "").strip()
        if not target:
            raise ValueError("ssh_target is required")
        if not re.fullmatch(r"[A-Za-z0-9_.@:-]+", target):
            raise ValueError("Invalid ssh_target format")

        base = (base_path or "~").strip()
        if "\n" in base or "\r" in base:
            raise ValueError("Invalid base_path")
        if not base:
            base = "~"

        remote_script = (
            f"BASE={shlex.quote(base)}; "
            "if [ \"$BASE\" = \"~\" ]; then BASE=\"$HOME\"; fi; "
            "BASE=$(cd \"$BASE\" 2>/dev/null && pwd -P || echo \"$BASE\"); "
            "PARENT=$(dirname \"$BASE\"); "
            "for ROOT in \"$BASE\" \"$PARENT\" \"$HOME/frappe\"; do "
            "  [ -d \"$ROOT\" ] || continue; "
            "  if [ -f \"$ROOT/sites/common_site_config.json\" ]; then printf '%s\n' \"$ROOT\"; fi; "
            "  find \"$ROOT\" -maxdepth 6 "
            "    \\( -name .git -o -name env -o -name venv -o -name .venv -o -name node_modules -o -name __pycache__ \\) -prune -o "
            "    -type f -path '*/sites/common_site_config.json' -print 2>/dev/null "
            "    | sed 's|/sites/common_site_config.json$||'; "
            "done | awk 'NF && !seen[$0]++' | sort -u"
        )
        proc = subprocess.run(
            self._build_ssh_command(target, ssh_password, remote_script),
            cwd=str(self.bench_path),
            capture_output=True,
            text=True,
            check=False,
            timeout=35,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "SSH command failed").strip()
            raise RuntimeError(err)

        benches = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return {
            "message": f"Fetched {len(benches)} bench folder(s) from {target}",
            "ssh_target": target,
            "benches": benches,
        }

    def _build_ssh_command(self, target: str, ssh_password: str, remote_script: str) -> List[str]:
        password = ssh_password or ""
        if password:
            sshpass_bin = shutil.which("sshpass")
            if not sshpass_bin:
                raise RuntimeError(
                    "Password-based SSH requires sshpass. Install it, or use SSH key-based login."
                )
            return [
                sshpass_bin,
                "-p",
                password,
                "ssh",
                "-o",
                "StrictHostKeyChecking=accept-new",
                target,
                remote_script,
            ]
        return ["ssh", "-o", "BatchMode=yes", target, remote_script]

    def _run_ssh_capture(
        self, target: str, ssh_password: str, remote_script: str, timeout: int = 35
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            self._build_ssh_command(target, ssh_password, remote_script),
            cwd=str(self.bench_path),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

    def _target_host(self, target: str) -> str:
        raw = (target or "").strip()
        if "@" in raw:
            raw = raw.split("@", 1)[1]
        return raw or "localhost"

    def _remote_common_meta(self, target: str, bench: str, ssh_password: str) -> Dict[str, object]:
        remote_script = (
            f"BENCH={shlex.quote(bench)}; export BENCH; "
            "python3 - <<'PY'\n"
            "import json, os, socket, pathlib, urllib.request\n"
            "bench = pathlib.Path(os.environ.get('BENCH', '.'))\n"
            "cfg = bench / 'sites' / 'common_site_config.json'\n"
            "common_port = 8000\n"
            "default_site = ''\n"
            "if cfg.exists():\n"
            "    try:\n"
            "        data = json.loads(cfg.read_text(errors='ignore'))\n"
            "        wp = data.get('webserver_port')\n"
            "        if isinstance(wp, int):\n"
            "            common_port = wp\n"
            "        elif isinstance(wp, str) and wp.isdigit():\n"
            "            common_port = int(wp)\n"
            "        ds = str(data.get('default_site', '')).strip()\n"
            "        if ds:\n"
            "            default_site = ds\n"
            "    except Exception:\n"
            "        pass\n"
            "if not default_site:\n"
            "    cur = bench / 'sites' / 'currentsite.txt'\n"
            "    if cur.exists():\n"
            "        try:\n"
            "            default_site = cur.read_text(errors='ignore').strip()\n"
            "        except Exception:\n"
            "            pass\n"
            "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            "s.settimeout(0.6)\n"
            "running = (s.connect_ex(('127.0.0.1', int(common_port))) == 0)\n"
            "s.close()\n"
            "if running and not default_site:\n"
            "    # Try to identify active site from response headers.\n"
            "    try:\n"
            "        req = urllib.request.Request(f'http://127.0.0.1:{int(common_port)}/api/method/ping')\n"
            "        with urllib.request.urlopen(req, timeout=1.8) as resp:\n"
            "            header_site = (resp.headers.get('X-Frappe-Site-Name') or resp.headers.get('x-frappe-site-name') or '').strip()\n"
            "            if header_site:\n"
            "                default_site = header_site\n"
            "    except Exception:\n"
            "        pass\n"
            "print(json.dumps({'common_port': int(common_port), 'default_site': default_site, 'common_running': bool(running)}))\n"
            "PY"
        )
        proc = self._run_ssh_capture(target, ssh_password, remote_script)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "SSH command failed").strip()
            raise RuntimeError(err)
        try:
            return json.loads((proc.stdout or "").strip() or "{}")
        except Exception as exc:
            raise RuntimeError(f"Could not parse remote bench metadata: {exc}") from exc

    def list_remote_sites(
        self, ssh_target: str, bench_path: str, ssh_password: str = ""
    ) -> Dict[str, object]:
        target = (ssh_target or "").strip()
        if not target:
            raise ValueError("ssh_target is required")
        if not re.fullmatch(r"[A-Za-z0-9_.@:-]+", target):
            raise ValueError("Invalid ssh_target format")

        bench = (bench_path or "").strip()
        if not bench:
            raise ValueError("bench_path is required")
        if "\n" in bench or "\r" in bench:
            raise ValueError("Invalid bench_path")

        remote_script = (
            f"BENCH={shlex.quote(bench)}; "
            "if [ ! -d \"$BENCH/sites\" ]; then "
            "  echo '__ERROR__: Bench sites directory not found'; "
            "  exit 2; "
            "fi; "
            "find \"$BENCH/sites\" -mindepth 1 -maxdepth 1 -type d "
            "! -name assets ! -name '.*' "
            "-printf '%f\\t%p\\n' | sort"
        )
        proc = self._run_ssh_capture(target, ssh_password, remote_script)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if proc.returncode != 0:
            err = (stderr or stdout or "SSH command failed").strip()
            raise RuntimeError(err)
        if "__ERROR__:" in stdout:
            raise RuntimeError(stdout.strip().replace("__ERROR__:", "").strip())

        ps_proc = self._run_ssh_capture(target, ssh_password, "ps -eo pid=,args=")
        if ps_proc.returncode != 0:
            err = (ps_proc.stderr or ps_proc.stdout or "Could not read remote process list").strip()
            raise RuntimeError(err)

        meta = self._remote_common_meta(target, bench, ssh_password)
        common_port = int(meta.get("common_port", 8000) or 8000)
        default_site = str(meta.get("default_site", "") or "")
        common_running = bool(meta.get("common_running", False))
        remote_host = self._target_host(target)

        custom_by_site: Dict[str, int] = {}
        for line in (ps_proc.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            _, cmdline = parts
            if "bench" not in cmdline or "serve" not in cmdline or "--site" not in cmdline:
                continue
            try:
                tokens = shlex.split(cmdline)
            except ValueError:
                continue
            site_name = self._parse_option_value(tokens, "--site")
            raw_port = self._parse_option_value(tokens, "--port")
            if not site_name:
                continue
            port = int(raw_port) if raw_port and raw_port.isdigit() else common_port
            custom_by_site[site_name] = port

        sites: List[Dict[str, str]] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            name, site_path = parts
            name = name.strip()
            status = "stopped"
            running_port: Optional[int] = None
            open_url: Optional[str] = None
            if name in custom_by_site:
                running_port = custom_by_site[name]
                status = "running_custom"
                open_url = f"{SITE_PROTOCOL}://{remote_host}:{running_port}"
            elif common_running and default_site == name:
                running_port = common_port
                status = "running_common"
                open_url = f"{SITE_PROTOCOL}://{remote_host}:{common_port}"
            sites.append(
                {
                    "name": name,
                    "site_path": site_path.strip(),
                    "configured_port": None,
                    "url_hint": "-",
                    "status": status,
                    "running_port": running_port,
                    "open_url": open_url,
                }
            )

        return {
            "message": f"Fetched {len(sites)} site(s) from {target}:{bench}",
            "ssh_target": target,
            "bench_path": bench,
            "remote_host": remote_host,
            "common_port": common_port,
            "common_running": common_running,
            "default_site": default_site,
            "sites": sites,
        }

    def run_remote_site(
        self, ssh_target: str, bench_path: str, site: str, port: int, ssh_password: str = ""
    ) -> Dict[str, object]:
        target = ssh_target.strip()
        bench = bench_path.strip()
        site_name = site.strip()
        if not target or not bench or not site_name:
            raise ValueError("ssh_target, bench_path and site are required")
        if port < 1 or port > 65535:
            raise ValueError("Port must be between 1 and 65535")

        cmd = (
            f"BENCH={shlex.quote(bench)}; SITE={shlex.quote(site_name)}; PORT={port}; export BENCH SITE PORT; "
            "if [ ! -d \"$BENCH/sites/$SITE\" ]; then echo '__ERROR__: Site not found'; exit 2; fi; "
            "python3 - <<'PY'\n"
            "import os, socket\n"
            "p = int(os.environ.get('PORT', '0'))\n"
            "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            "s.settimeout(0.6)\n"
            "busy = (s.connect_ex(('127.0.0.1', p)) == 0)\n"
            "s.close()\n"
            "print('BUSY' if busy else 'FREE')\n"
            "PY"
        )
        chk = self._run_ssh_capture(target, ssh_password, cmd)
        if chk.returncode != 0:
            err = (chk.stderr or chk.stdout or "SSH command failed").strip()
            raise RuntimeError(err)
        if "__ERROR__:" in (chk.stdout or ""):
            raise RuntimeError((chk.stdout or "").strip().replace("__ERROR__:", "").strip())
        if "BUSY" in (chk.stdout or ""):
            raise ValueError(f"Port {port} is already in use on remote host")

        safe_site = re.sub(r"[^A-Za-z0-9_.-]", "_", site_name)
        start_script = (
            f"BENCH={shlex.quote(bench)}; SITE={shlex.quote(site_name)}; PORT={port}; "
            "mkdir -p \"$BENCH/.bench_panel_runtime\"; "
            f"LOG=\"$BENCH/.bench_panel_runtime/{safe_site}_{port}.log\"; "
            "cd \"$BENCH\" && (nohup bench --site \"$SITE\" serve --port \"$PORT\" --noreload --nothreading > \"$LOG\" 2>&1 < /dev/null &) ; "
            "echo started"
        )
        try:
            started = self._run_ssh_capture(target, ssh_password, start_script, timeout=12)
            if started.returncode != 0:
                err = (started.stderr or started.stdout or "Failed to start remote site").strip()
                raise RuntimeError(err)
        except subprocess.TimeoutExpired:
            # Detached SSH start may keep session briefly; verify by probing port.
            pass

        # Verify port becomes reachable to confirm remote site actually started.
        check_script = (
            f"PORT={port}; export PORT; "
            "python3 - <<'PY'\n"
            "import os, socket\n"
            "p = int(os.environ.get('PORT', '0'))\n"
            "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            "s.settimeout(0.8)\n"
            "ok = (s.connect_ex(('127.0.0.1', p)) == 0)\n"
            "s.close()\n"
            "print('UP' if ok else 'DOWN')\n"
            "PY"
        )
        for _ in range(10):
            time.sleep(0.8)
            probe = self._run_ssh_capture(target, ssh_password, check_script, timeout=8)
            if probe.returncode == 0 and "UP" in (probe.stdout or ""):
                return {
                    "message": f"Started remote site {site_name} on {SITE_PROTOCOL}://{self._target_host(target)}:{port}",
                    "site": site_name,
                    "port": port,
                }
        raise RuntimeError(f"Start command sent but remote site {site_name} did not bind port {port} in time.")

    def stop_remote_site(
        self, ssh_target: str, bench_path: str, site: str, ssh_password: str = ""
    ) -> Dict[str, object]:
        target = ssh_target.strip()
        bench = bench_path.strip()
        site_name = site.strip()
        if not target or not bench or not site_name:
            raise ValueError("ssh_target, bench_path and site are required")

        stop_script = (
            f"BENCH={shlex.quote(bench)}; SITE={shlex.quote(site_name)}; export BENCH SITE; "
            "python3 - <<'PY'\n"
            "import os, shlex, signal, subprocess\n"
            "site = os.environ.get('SITE', '')\n"
            "p = subprocess.run(['ps','-eo','pid=,args='], capture_output=True, text=True, check=False)\n"
            "killed = 0\n"
            "for line in p.stdout.splitlines():\n"
            "    line = line.strip()\n"
            "    if not line:\n"
            "        continue\n"
            "    parts = line.split(maxsplit=1)\n"
            "    if len(parts) != 2:\n"
            "        continue\n"
            "    pid_text, cmd = parts\n"
            "    if 'bench' not in cmd or 'serve' not in cmd or '--site' not in cmd:\n"
            "        continue\n"
            "    try:\n"
            "        tokens = shlex.split(cmd)\n"
            "    except Exception:\n"
            "        continue\n"
            "    found = None\n"
            "    for i,t in enumerate(tokens):\n"
            "        if t == '--site' and i + 1 < len(tokens):\n"
            "            found = tokens[i+1]\n"
            "            break\n"
            "        if t.startswith('--site='):\n"
            "            found = t.split('=',1)[1]\n"
            "            break\n"
            "    if found != site:\n"
            "        continue\n"
            "    pid = int(pid_text)\n"
            "    try:\n"
            "        os.kill(pid, signal.SIGTERM)\n"
            "        killed += 1\n"
            "    except Exception:\n"
            "        pass\n"
            "print(killed)\n"
            "PY"
        )
        stopped = self._run_ssh_capture(target, ssh_password, stop_script)
        if stopped.returncode != 0:
            err = (stopped.stderr or stopped.stdout or "Failed to stop remote site").strip()
            raise RuntimeError(err)
        killed = (stopped.stdout or "").strip() or "0"
        if killed == "0":
            # Fallback: pattern kill can catch wrapper cmdlines the parser misses.
            fallback_script = (
                f"SITE={shlex.quote(site_name)}; export SITE; "
                "pkill -f \"bench --site $SITE serve\" >/dev/null 2>&1 || true; "
                "pkill -f \"--site $SITE serve\" >/dev/null 2>&1 || true; "
                "echo fallback"
            )
            self._run_ssh_capture(target, ssh_password, fallback_script, timeout=10)
        return {"message": f"Stop signal sent for remote site {site_name}. Matched processes: {killed}"}

    def start_remote_bench(self, ssh_target: str, bench_path: str, ssh_password: str = "") -> Dict[str, object]:
        target = ssh_target.strip()
        bench = bench_path.strip()
        if not target or not bench:
            raise ValueError("ssh_target and bench_path are required")
        meta = self._remote_common_meta(target, bench, ssh_password)
        common_port = int(meta.get("common_port", 8000) or 8000)
        if bool(meta.get("common_running", False)):
            return {"message": f"Remote bench/common port already reachable on {SITE_PROTOCOL}://{self._target_host(target)}:{common_port}"}
        start_script = (
            f"BENCH={shlex.quote(bench)}; PORT={common_port}; "
            "mkdir -p \"$BENCH/.bench_panel_runtime\"; "
            "cd \"$BENCH\" && (nohup bench start "
            "> \"$BENCH/.bench_panel_runtime/bench_remote.log\" 2>&1 < /dev/null &) ; "
            "echo started"
        )
        try:
            proc = self._run_ssh_capture(target, ssh_password, start_script, timeout=12)
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "Failed to start remote bench").strip()
                raise RuntimeError(err)
        except subprocess.TimeoutExpired:
            # Detached launch can outlive SSH command timeout; validate using port probe below.
            pass

        # Give remote process a short window to bind common port before declaring failure.
        for _ in range(10):
            time.sleep(1.0)
            try:
                recheck = self._remote_common_meta(target, bench, ssh_password)
            except Exception:
                continue
            if bool(recheck.get("common_running", False)):
                return {
                    "message": f"Remote bench started on {SITE_PROTOCOL}://{self._target_host(target)}:{common_port}"
                }
        raise RuntimeError(
            "Start command sent but remote common port did not become reachable yet. "
            "Check remote .bench_panel_runtime/bench_remote.log"
        )

    def stop_remote_bench(self, ssh_target: str, bench_path: str, ssh_password: str = "") -> Dict[str, object]:
        target = ssh_target.strip()
        bench = bench_path.strip()
        if not target or not bench:
            raise ValueError("ssh_target and bench_path are required")
        stop_script = (
            f"BENCH={shlex.quote(bench)}; "
            "cd \"$BENCH\" && bench stop >/dev/null 2>&1 || true; "
            "pkill -f 'bench serve' >/dev/null 2>&1 || true; "
            "echo done"
        )
        proc = self._run_ssh_capture(target, ssh_password, stop_script)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "Failed to stop remote bench").strip()
            raise RuntimeError(err)
        return {"message": "Remote bench stop command executed."}

    def force_stop_all_remote(
        self,
        ssh_target: str,
        bench_path: str,
        ssh_password: str = "",
        sudo_password: str = "",
    ) -> Dict[str, object]:
        target = (ssh_target or "").strip()
        if not target:
            raise ValueError("ssh_target is required")
        if not ssh_password:
            raise ValueError("SSH password is required for remote force stop")

        # Prefer explicitly provided sudo password; fallback to ssh password.
        sudo_pass = sudo_password or ssh_password
        remote_cmd = (
            "bash -lc \"printf '%s\\n' "
            + shlex.quote(sudo_pass)
            + " | sudo -S pkill -f 'frappe'; "
              "printf '%s\\n' "
            + shlex.quote(sudo_pass)
            + " | sudo -S pkill redis-server\""
        )
        proc = self._run_ssh_capture(target, ssh_password, remote_cmd, timeout=35)
        stderr = (proc.stderr or "").strip().lower()
        if "incorrect password" in stderr or "try again" in stderr or "authentication failure" in stderr:
            raise RuntimeError("Incorrect remote sudo password")
        if proc.returncode not in (0, 1):
            err = (proc.stderr or proc.stdout or "Remote force stop command failed").strip()
            raise RuntimeError(err)

        return {"message": f"Remote force stop executed on {target}."}

    def detect_access_host(self) -> str:
        env_host = os.environ.get("BENCH_PUBLIC_HOST")
        if env_host:
            return env_host.strip()

        if self.access_host_override:
            return self.access_host_override

        ssh_connection = os.environ.get("SSH_CONNECTION", "").strip()
        if ssh_connection:
            parts = ssh_connection.split()
            if len(parts) >= 3:
                ssh_server_host = parts[2].strip()
                if ssh_server_host:
                    return ssh_server_host

        try:
            hostname = socket.gethostname().strip()
            if hostname:
                return hostname
        except Exception:
            pass

        return "localhost"

    def _run_command(
        self,
        command: List[str],
        *,
        stdout_path: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> subprocess.Popen:
        stdout_handle = open(stdout_path, "a", buffering=1) if stdout_path else subprocess.DEVNULL
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        try:
            process = subprocess.Popen(
                command,
                cwd=str(self.bench_path),
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
                env=merged_env,
            )
        finally:
            if stdout_path and hasattr(stdout_handle, "close"):
                stdout_handle.close()
        return process

    def _bench_command_prefix(self) -> List[str]:
        candidates = [
            self.bench_path / "env" / "bin" / "bench",
            self.bench_path / "bin" / "bench",
        ]
        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return [str(candidate)]

        which_bench = shutil.which("bench")
        if which_bench:
            return [which_bench]

        raise RuntimeError(
            "Could not find bench executable. Expected one of: "
            f"{self.bench_path / 'env' / 'bin' / 'bench'}, "
            f"{self.bench_path / 'bin' / 'bench'} or bench in PATH."
        )

    def _is_process_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _port_in_use(self, port: int, host: str = "127.0.0.1") -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.7)
            return sock.connect_ex((host, port)) == 0

    def _wait_for_port(self, port: int, timeout_seconds: int = 45, process: Optional[subprocess.Popen] = None) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if self._port_in_use(port):
                return True
            if process and process.poll() is not None:
                return False
            time.sleep(0.5)
        return self._port_in_use(port)

    def _terminate_pid(self, pid: int) -> None:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            time.sleep(1)
            if self._is_process_running(pid):
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except ProcessLookupError:
            return

    def _tail_file(self, path: Path, lines: int = 20) -> str:
        try:
            content = path.read_text(errors="ignore").splitlines()
            return "\n".join(content[-lines:])
        except Exception:
            return ""

    def _save_state(self) -> None:
        data = [asdict(server) for server in self.site_servers.values() if self._is_process_running(server.pid)]
        self.state_file.write_text(json.dumps(data, indent=2))

    def _restore_state(self) -> None:
        if not self.state_file.exists():
            return

        try:
            data = json.loads(self.state_file.read_text())
            for row in data:
                server = SiteServer(**row)
                if self._is_process_running(server.pid):
                    self.site_servers[server.site] = server
            if self.site_servers:
                self.log(f"Restored {len(self.site_servers)} running custom site server(s) from state.")
        except Exception as exc:
            self.log(f"Could not restore state: {exc}")

    def _get_common_webserver_port(self) -> int:
        config_file = self.sites_path / DEFAULT_COMMON_SITE_CONFIG
        if not config_file.exists():
            return 8000

        try:
            data = json.loads(config_file.read_text())
            webserver_port = data.get("webserver_port")
            if isinstance(webserver_port, int):
                return webserver_port
            if isinstance(webserver_port, str) and webserver_port.isdigit():
                return int(webserver_port)
        except Exception:
            pass

        return 8000

    def _build_public_url(self, port: int) -> str:
        return f"{SITE_PROTOCOL}://{self.detect_access_host()}:{port}"

    def common_port_running(self) -> bool:
        return self._port_in_use(self._get_common_webserver_port(), "127.0.0.1")

    def _parse_option_value(self, tokens: List[str], option: str) -> Optional[str]:
        for idx, token in enumerate(tokens):
            if token == option and idx + 1 < len(tokens):
                return tokens[idx + 1]
            if token.startswith(f"{option}="):
                return token.split("=", 1)[1]
        return None

    def _detect_site_on_port(self, port: int) -> Optional[str]:
        try:
            proc = subprocess.run(
                ["ps", "-eo", "pid=,args="],
                cwd=str(self.bench_path),
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return None

        if proc.returncode != 0:
            return None

        detected_sites: List[str] = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            _, cmdline = parts

            if "bench serve" not in cmdline:
                continue

            try:
                tokens = shlex.split(cmdline)
            except ValueError:
                continue

            if "serve" not in tokens:
                continue

            raw_port = self._parse_option_value(tokens, "--port")
            parsed_port = int(raw_port) if raw_port and raw_port.isdigit() else self._get_common_webserver_port()
            if parsed_port != port:
                continue

            site = self._parse_option_value(tokens, "--site")
            if site:
                detected_sites.append(site)

        if len(detected_sites) == 1:
            return detected_sites[0]

        if port == self._get_common_webserver_port():
            config_file = self.sites_path / DEFAULT_COMMON_SITE_CONFIG
            if config_file.exists():
                try:
                    config_data = json.loads(config_file.read_text())
                    default_site = str(config_data.get("default_site", "")).strip()
                    if default_site:
                        return default_site
                except Exception:
                    pass

            current_site_file = self.sites_path / "currentsite.txt"
            if current_site_file.exists():
                try:
                    current_site = current_site_file.read_text().strip()
                    if current_site:
                        return current_site
                except Exception:
                    pass

        return None

    def list_sites(self) -> List[Dict[str, Optional[str]]]:
        results: List[Dict[str, Optional[str]]] = []
        common_port = self._get_common_webserver_port()
        public_url = self._build_public_url(common_port)

        if not self.sites_path.exists():
            return results

        for item in sorted(self.sites_path.iterdir()):
            if not item.is_dir():
                continue
            if item.name == "assets":
                continue
            if item.name.startswith("."):
                continue

            results.append(
                {
                    "name": item.name,
                    "site_path": str(item),
                    "configured_port": None,
                    "url_hint": public_url,
                }
            )

        return results

    def start_bench(self) -> Dict[str, str]:
        with self.lock:
            common_port = self._get_common_webserver_port()

            if self.common_port_running():
                return {"message": f"Bench/common port already reachable on {self._build_public_url(common_port)}"}

            start_command = [*self._bench_command_prefix(), "start"]
            self.log(f"Starting bench: {' '.join(start_command)}")
            self.bench_process = self._run_command(start_command, stdout_path=self.bench_log)

            if self._wait_for_port(common_port, timeout_seconds=50, process=self.bench_process):
                return {"message": f"Bench started successfully on {self._build_public_url(common_port)}"}

            tail = self._tail_file(self.bench_log, lines=30)
            raise RuntimeError(
                "Bench start failed or is incomplete. "
                "The panel no longer falls back to 'bench serve' because that breaks Desk login (Redis/worker missing). "
                "Check .bench_panel_runtime/bench.log.\n"
                f"Last log lines:\n{tail}"
            )

    def stop_bench(self) -> Dict[str, str]:
        with self.lock:
            if self.bench_process and self.bench_process.poll() is None:
                self.log("Stopping bench process group.")
                self._terminate_pid(self.bench_process.pid)

                self.bench_process = None
                return {"message": "Bench stopped successfully."}

            return {"message": "Bench was not started by this panel. If port 8000 is still active, stop it manually."}

    def stop_all_for_switch(self) -> Dict[str, object]:
        with self.lock:
            stopped_site_servers = 0
            for site, server in list(self.site_servers.items()):
                if self._is_process_running(server.pid):
                    self._terminate_pid(server.pid)
                    stopped_site_servers += 1
                self.site_servers.pop(site, None)
                self.site_processes.pop(site, None)

            self.site_processes.clear()
            self._save_state()

            stopped_panel_bench = False
            if self.bench_process and self.bench_process.poll() is None:
                self._terminate_pid(self.bench_process.pid)
                stopped_panel_bench = True
            self.bench_process = None

        bench_stop_rc: Optional[int] = None
        bench_stop_error: Optional[str] = None
        try:
            stop_cmd = [*self._bench_command_prefix(), "stop"]
            proc = subprocess.run(
                stop_cmd,
                cwd=str(self.bench_path),
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            bench_stop_rc = proc.returncode
        except Exception as exc:
            bench_stop_error = str(exc)

        return {
            "stopped_site_servers": stopped_site_servers,
            "stopped_panel_bench": stopped_panel_bench,
            "bench_stop_returncode": bench_stop_rc,
            "bench_stop_error": bench_stop_error,
        }

    def _find_free_port(self, start: int = 3434, end: int = 3999) -> int:
        common_port = self._get_common_webserver_port()
        busy_ports = {server.port for server in self.site_servers.values() if self._is_process_running(server.pid)}

        for candidate in range(start, end + 1):
            if candidate == common_port:
                continue
            if candidate in busy_ports:
                continue
            if not self._port_in_use(candidate):
                return candidate

        raise RuntimeError(f"No free port found in range {start}-{end}")

    def run_site(self, site: str, port: int) -> Dict[str, str]:
        with self.lock:
            if not any(x["name"] == site for x in self.list_sites()):
                raise ValueError(f"Site not found: {site}")

            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
            chosen_port = port

            existing = self.site_servers.get(site)
            if existing and self._is_process_running(existing.pid):
                return {"message": f"Site {site} is already running on {self._build_public_url(existing.port)}"}

            if self._port_in_use(chosen_port):
                raise ValueError(f"Port {chosen_port} is already in use")

            log_file = self.runtime_dir / f"{site.replace('.', '_')}_{chosen_port}.log"
            command = [
                *self._bench_command_prefix(),
                "--site",
                site,
                "serve",
                "--port",
                str(chosen_port),
                "--noreload",
                "--nothreading",
            ]
            self.log(f"Running site {site} on port {chosen_port}: {' '.join(shlex.quote(x) for x in command)}")
            proc = self._run_command(command, stdout_path=log_file)

            started = False
            for _ in range(60):
                if proc.poll() is not None:
                    break
                if self._port_in_use(chosen_port):
                    started = True
                    break
                time.sleep(0.5)

            if not started:
                if proc.poll() is None:
                    self._terminate_pid(proc.pid)
                raise RuntimeError(f"Site server failed to start for {site}. Check {log_file}")

            server = SiteServer(
                site=site,
                port=chosen_port,
                pid=proc.pid,
                started_at=datetime.now().isoformat(timespec="seconds"),
                command=command,
                log_file=str(log_file),
            )
            self.site_processes[site] = proc
            self.site_servers[site] = server
            self._save_state()

            return {"message": f"Site {site} is running on {self._build_public_url(chosen_port)}"}

    def stop_site(self, site: str) -> Dict[str, str]:
        with self.lock:
            server = self.site_servers.get(site)
            if not server:
                return {"message": f"Site {site} is not running from this panel."}

            if not self._is_process_running(server.pid):
                self.site_servers.pop(site, None)
                self.site_processes.pop(site, None)
                self._save_state()
                return {"message": f"Site {site} process already stopped."}

            self.log(f"Stopping site {site} on port {server.port} (pid {server.pid}).")
            self._terminate_pid(server.pid)

            self.site_servers.pop(site, None)
            self.site_processes.pop(site, None)
            self._save_state()

            return {"message": f"Stopped site {site}."}

    def force_stop_all_sites(self, sudo_password: str) -> Dict[str, str]:
        if not sudo_password:
            raise ValueError("Sudo password is required")

        # Execute the exact stop intent requested by user:
        # sudo pkill -f "frappe" && sudo pkill redis-server
        cmd = 'sudo -S pkill -f "frappe" && sudo -S pkill redis-server'
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=str(self.bench_path),
            input=f"{sudo_password}\n{sudo_password}\n",
            capture_output=True,
            text=True,
            check=False,
        )

        stderr = (proc.stderr or "").strip().lower()
        if "incorrect password" in stderr or "try again" in stderr or "authentication failure" in stderr:
            raise RuntimeError("Incorrect sudo password")

        # pkill returns non-zero if no process matched; treat that as non-fatal.
        if proc.returncode not in (0, 1):
            raise RuntimeError((proc.stderr or proc.stdout or "Force stop command failed").strip())

        with self.lock:
            self.site_servers.clear()
            self.site_processes.clear()
            self.bench_process = None
            self._save_state()

        return {"message": "Force stop command executed successfully."}

    def get_logs(self) -> List[str]:
        lines: List[str] = []

        if self.bench_log.exists():
            try:
                bench_lines = self.bench_log.read_text(errors="ignore").splitlines()[-80:]
                lines.extend([f"[bench.log] {line}" for line in bench_lines])
            except Exception as exc:
                lines.append(f"Could not read bench log: {exc}")

        lines.extend(self.logs[-200:])
        return lines[-250:]

    def get_site_live_log(self, site: str, lines: int = 120) -> Dict[str, object]:
        site_name = (site or "").strip()
        if not site_name:
            raise ValueError("site is required")
        max_lines = max(20, min(int(lines or 120), 400))
        self.cleanup_dead_processes()
        server = self.site_servers.get(site_name)
        if not server:
            raise ValueError(f"Site {site_name} is not running from this panel")

        log_path = Path(server.log_file)
        out = []
        if log_path.exists():
            out = log_path.read_text(errors="ignore").splitlines()[-max_lines:]
        return {
            "site": site_name,
            "port": server.port,
            "logs": out,
        }

    def get_remote_site_live_log(
        self,
        ssh_target: str,
        bench_path: str,
        site: str,
        port: int,
        ssh_password: str = "",
        lines: int = 120,
    ) -> Dict[str, object]:
        target = (ssh_target or "").strip()
        bench = (bench_path or "").strip()
        site_name = (site or "").strip()
        if not target or not bench or not site_name:
            raise ValueError("ssh_target, bench_path and site are required")
        if port < 1 or port > 65535:
            raise ValueError("port must be between 1 and 65535")
        max_lines = max(20, min(int(lines or 120), 400))
        safe_site = re.sub(r"[^A-Za-z0-9_.-]", "_", site_name)

        remote_script = (
            f"BENCH={shlex.quote(bench)}; SITE_SAFE={shlex.quote(safe_site)}; PORT={port}; LINES={max_lines}; "
            "LOG=\"$BENCH/.bench_panel_runtime/${SITE_SAFE}_${PORT}.log\"; "
            "if [ ! -f \"$LOG\" ]; then echo '__ERROR__: log file not found'; exit 2; fi; "
            "tail -n \"$LINES\" \"$LOG\""
        )
        proc = self._run_ssh_capture(target, ssh_password, remote_script, timeout=20)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "Remote live log failed").strip()
            if "__ERROR__:" in err:
                err = err.replace("__ERROR__:", "").strip()
            raise RuntimeError(err)
        return {
            "site": site_name,
            "port": port,
            "logs": (proc.stdout or "").splitlines()[-max_lines:],
        }

    def cleanup_dead_processes(self) -> None:
        removed = []
        for site, server in list(self.site_servers.items()):
            if not self._is_process_running(server.pid) or not self._port_in_use(server.port):
                removed.append(site)
                self.site_servers.pop(site, None)
                self.site_processes.pop(site, None)

        if removed:
            self.log(f"Removed dead site servers from state: {', '.join(removed)}")
            self._save_state()

    def status(self) -> Dict[str, object]:
        self.cleanup_dead_processes()
        common_port = self._get_common_webserver_port()
        access_host = self.detect_access_host()
        common_site = self._detect_site_on_port(common_port) if self.common_port_running() else None

        return {
            "bench_running": bool(self.bench_process and self.bench_process.poll() is None),
            "common_port_running": self.common_port_running(),
            "sites": self.list_sites(),
            "running_site_servers": [asdict(x) for x in self.site_servers.values()],
            "common_port": common_port,
            "common_port_site": common_site,
            "access_host": access_host,
            "protocol": SITE_PROTOCOL,
            "public_base_url": f"{SITE_PROTOCOL}://{access_host}:{common_port}",
        }


manager: Optional[BenchManager] = None
manager_switch_lock = threading.RLock()


def login_required() -> bool:
    return bool(session.get("logged_in"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        if request.form.get("password") == PANEL_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Invalid password"

    return render_template_string(HTML_TEMPLATE, login=True, error=error, title=APP_TITLE)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if not login_required():
        return redirect(url_for("login"))

    assert manager is not None
    return render_template_string(
        HTML_TEMPLATE,
        login=False,
        title=APP_TITLE,
        bench_path=str(manager.bench_path),
        sites=manager.list_sites(),
        access_host=manager.detect_access_host(),
        common_port=manager._get_common_webserver_port(),
    )


@app.route("/api/status")
def api_status():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    return jsonify(manager.status())


@app.route("/api/bench/paths")
def api_bench_paths():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    try:
        return jsonify(manager.list_local_bench_paths())
    except Exception as exc:
        manager.log(f"Bench path list failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/access-host", methods=["POST"])
def api_access_host():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    host = str(payload.get("host", ""))
    try:
        return jsonify(manager.set_access_host(host))
    except Exception as exc:
        manager.log(f"Access host update failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/benches", methods=["POST"])
def api_ssh_benches():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    base_path = str(payload.get("base_path", "~")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    try:
        return jsonify(manager.list_remote_bench_folders(ssh_target, base_path, ssh_password))
    except Exception as exc:
        manager.log(f"Remote bench browse failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/sites", methods=["POST"])
def api_ssh_sites():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    try:
        return jsonify(manager.list_remote_sites(ssh_target, bench_path, ssh_password))
    except Exception as exc:
        manager.log(f"Remote site list failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/bench/start", methods=["POST"])
def api_ssh_bench_start():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    try:
        return jsonify(manager.start_remote_bench(ssh_target, bench_path, ssh_password))
    except Exception as exc:
        manager.log(f"Remote bench start failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/bench/stop", methods=["POST"])
def api_ssh_bench_stop():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    try:
        return jsonify(manager.stop_remote_bench(ssh_target, bench_path, ssh_password))
    except Exception as exc:
        manager.log(f"Remote bench stop failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/site/run", methods=["POST"])
def api_ssh_site_run():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    site = str(payload.get("site", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    raw_port = payload.get("port")
    try:
        port = int(raw_port)
    except Exception:
        return jsonify({"error": "Port must be a valid number"}), 400
    try:
        return jsonify(manager.run_remote_site(ssh_target, bench_path, site, port, ssh_password))
    except Exception as exc:
        manager.log(f"Remote site run failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/site/stop", methods=["POST"])
def api_ssh_site_stop():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    site = str(payload.get("site", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    try:
        return jsonify(manager.stop_remote_site(ssh_target, bench_path, site, ssh_password))
    except Exception as exc:
        manager.log(f"Remote site stop failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/site/live-log", methods=["POST"])
def api_ssh_site_live_log():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    site = str(payload.get("site", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    raw_port = payload.get("port")
    raw_lines = payload.get("lines", 120)
    try:
        port = int(raw_port)
    except Exception:
        return jsonify({"error": "port is required and must be a number"}), 400
    try:
        lines = int(raw_lines)
    except Exception:
        lines = 120
    try:
        return jsonify(manager.get_remote_site_live_log(ssh_target, bench_path, site, port, ssh_password, lines))
    except Exception as exc:
        manager.log(f"Remote site live log failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ssh/force-stop-all", methods=["POST"])
def api_ssh_force_stop_all():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    ssh_target = str(payload.get("ssh_target", "")).strip()
    bench_path = str(payload.get("bench_path", "")).strip()
    ssh_password = str(payload.get("ssh_password", ""))
    sudo_password = str(payload.get("sudo_password", ""))
    try:
        return jsonify(manager.force_stop_all_remote(ssh_target, bench_path, ssh_password, sudo_password))
    except Exception as exc:
        manager.log(f"Remote force stop failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/logs")
def api_logs():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    return jsonify({"logs": manager.get_logs()})


@app.route("/api/site/live-log")
def api_site_live_log():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    site = str(request.args.get("site", "")).strip()
    raw_lines = request.args.get("lines", "120")
    try:
        lines = int(raw_lines)
    except Exception:
        lines = 120
    try:
        return jsonify(manager.get_site_live_log(site, lines))
    except Exception as exc:
        manager.log(f"Site live log failed: {exc}")
        return jsonify({"error": str(exc)}), 400


@app.route("/api/bench/start", methods=["POST"])
def api_bench_start():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    try:
        return jsonify(manager.start_bench())
    except Exception as exc:
        manager.log(f"Bench start failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/bench/stop", methods=["POST"])
def api_bench_stop():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    try:
        return jsonify(manager.stop_bench())
    except Exception as exc:
        manager.log(f"Bench stop failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/bench/switch", methods=["POST"])
def api_bench_switch():
    global manager

    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(force=True) or {}
    raw_path = str(payload.get("bench_path", "")).strip()
    if not raw_path:
        return jsonify({"error": "bench_path is required"}), 400

    raw_stop = payload.get("stop_existing", False)
    if isinstance(raw_stop, bool):
        stop_existing = raw_stop
    else:
        stop_existing = str(raw_stop).strip().lower() in {"1", "true", "yes", "y", "on"}

    try:
        next_bench = validate_bench_path(raw_path)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    with manager_switch_lock:
        assert manager is not None
        current_manager = manager
        current_path = current_manager.bench_path.resolve()

        if next_bench.resolve() == current_path:
            return jsonify({"message": f"Already using bench folder: {current_path}"})

        stop_summary: Optional[Dict[str, object]] = None
        if stop_existing:
            stop_summary = current_manager.stop_all_for_switch()

        manager = BenchManager(str(next_bench))
        manager.log(f"Switched bench folder from {current_path} to {next_bench}")
        if stop_summary is not None:
            manager.log(
                "Stopped old bench context before switch: "
                f"site_servers={stop_summary['stopped_site_servers']}, "
                f"panel_bench_stopped={stop_summary['stopped_panel_bench']}, "
                f"bench_stop_rc={stop_summary['bench_stop_returncode']}"
            )
            if stop_summary.get("bench_stop_error"):
                manager.log(f"bench stop error on old context: {stop_summary['bench_stop_error']}")
            return jsonify(
                {
                    "message": f"Stopped old bench processes and switched to: {next_bench}",
                    "bench_path": str(next_bench),
                    "stopped": stop_summary,
                }
            )

        manager.log("Old bench context left running by user choice.")
        return jsonify(
            {
                "message": f"Switched to: {next_bench}. Old bench processes kept running.",
                "bench_path": str(next_bench),
            }
        )


@app.route("/api/site/run", methods=["POST"])
def api_site_run():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    site = str(payload.get("site", "")).strip()
    raw_port = payload.get("port")
    if raw_port is None or str(raw_port).strip() == "":
        return jsonify({"error": "Port is required"}), 400
    try:
        port = int(raw_port)
    except (TypeError, ValueError):
        return jsonify({"error": "Port must be a valid number"}), 400
    if port < 1 or port > 65535:
        return jsonify({"error": "Port must be between 1 and 65535"}), 400

    try:
        return jsonify(manager.run_site(site, port))
    except Exception as exc:
        manager.log(f"Run site failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/site/stop", methods=["POST"])
def api_site_stop():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    site = str(payload.get("site", "")).strip()

    try:
        return jsonify(manager.stop_site(site))
    except Exception as exc:
        manager.log(f"Stop site failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/site/force-stop-all", methods=["POST"])
def api_site_force_stop_all():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    assert manager is not None
    payload = request.get_json(force=True) or {}
    sudo_password = str(payload.get("sudo_password", ""))
    if not sudo_password:
        return jsonify({"error": "sudo_password is required"}), 400

    try:
        return jsonify(manager.force_stop_all_sites(sudo_password))
    except Exception as exc:
        manager.log(f"Force stop all sites failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/open-site/<site>")
def open_site(site: str):
    if not login_required():
        return redirect(url_for("login"))

    assert manager is not None
    manager.cleanup_dead_processes()

    custom = manager.site_servers.get(site)
    if custom and manager._port_in_use(custom.port):
        return redirect(manager._build_public_url(custom.port))
    common_port = manager._get_common_webserver_port()
    common_site = manager._detect_site_on_port(common_port) if manager.common_port_running() else None
    if common_site == site:
        return redirect(manager._build_public_url(common_port))

    return redirect(url_for("index"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Frappe Bench Control Panel")
    parser.add_argument("--bench", required=True, help="Absolute path to frappe bench")
    parser.add_argument("--host", default="127.0.0.1", help="Flask bind host")
    parser.add_argument("--port", type=int, default=5055, help="Flask bind port")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    return parser.parse_args()


def validate_bench_path(path: str) -> Path:
    bench = Path(path).resolve()

    if not bench.exists():
        raise FileNotFoundError(f"Bench path does not exist: {bench}")

    if not (bench / "sites").exists():
        raise FileNotFoundError(f"Not a valid bench path. Missing sites directory in: {bench}")

    return bench


def main() -> None:
    global manager

    args = parse_args()
    bench = validate_bench_path(args.bench)
    manager = BenchManager(str(bench))
    manager.log(f"Panel started for bench: {bench}")
    manager.log(f"Detected public host: {manager.detect_access_host()}")
    manager.log(f"Detected common bench port: {manager._get_common_webserver_port()}")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
