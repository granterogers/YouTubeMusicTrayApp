#!/usr/bin/env python3
"""
deploy_YTray.py  v1.3.0  -  Self-contained one-click builder + GitHub publisher
--------------------------------------------------------------------
Extracts all source files, builds a portable Windows .exe,
cleans up the build folder, then optionally pushes to GitHub.

Requirements: Node.js + npm  (https://nodejs.org)

Usage:
  python deploy_YTray.py                  # build + prompt to push
  python deploy_YTray.py --skip-build     # push to GitHub only
  python deploy_YTray.py --version 1.4.0  # override version
  python deploy_YTray.py --out C:\\Builds  # custom output folder

GitHub token: set GITHUB_TOKEN env var, or enter when prompted.
"""

import argparse, base64, json, os, re, shutil, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

REPO_OWNER = "granterogers"
REPO_NAME  = "YTray"
REPO_DESC  = "Lightweight YouTube tray player with global shortcuts"

# ── Embedded source files (base64) ───────────────────────────────────────────

FILES = {
    "main.js": "Y29uc3QgeyBhcHAsIEJyb3dzZXJXaW5kb3csIFRyYXksIE1lbnUsIGdsb2JhbFNob3J0Y3V0LCBuYXRpdmVJbWFnZSwgd2ViQ29udGVudHMgfSA9IHJlcXVpcmUoJ2VsZWN0cm9uJyk7CmNvbnN0IHBhdGggPSByZXF1aXJlKCdwYXRoJyk7CgovLyBQcmV2ZW50IGJhY2tncm91bmQgdGhyb3R0bGluZyBnbG9iYWxseSDigJQgdGhpcyBpcyB0aGUga2V5IGZpeAphcHAuY29tbWFuZExpbmUuYXBwZW5kU3dpdGNoKCdkaXNhYmxlLXJlbmRlcmVyLWJhY2tncm91bmRpbmcnKTsKYXBwLmNvbW1hbmRMaW5lLmFwcGVuZFN3aXRjaCgnZGlzYWJsZS1iYWNrZ3JvdW5kLXRpbWVyLXRocm90dGxpbmcnKTsKYXBwLmNvbW1hbmRMaW5lLmFwcGVuZFN3aXRjaCgnZGlzYWJsZS1iYWNrZ3JvdW5kaW5nLW9jY2x1ZGVkLXdpbmRvd3MnKTsKCmxldCB0cmF5ID0gbnVsbDsKbGV0IHdpbiA9IG51bGw7Cgpjb25zdCBTSE9SVENVVCA9ICdDb21tYW5kT3JDb250cm9sK0FsdCtTcGFjZSc7CmNvbnN0IFdJRFRIID0gNDYwOwpjb25zdCBIRUlHSFQgPSA2MDA7CgpmdW5jdGlvbiBjcmVhdGVXaW5kb3coKSB7CiAgd2luID0gbmV3IEJyb3dzZXJXaW5kb3coewogICAgd2lkdGg6IFdJRFRILAogICAgaGVpZ2h0OiBIRUlHSFQsCiAgICBzaG93OiBmYWxzZSwKICAgIGZyYW1lOiBmYWxzZSwKICAgIHJlc2l6YWJsZTogdHJ1ZSwKICAgIHNraXBUYXNrYmFyOiB0cnVlLAogICAgYWx3YXlzT25Ub3A6IGZhbHNlLAogICAgYmFja2dyb3VuZENvbG9yOiAnIzBmMGYwZicsCiAgICB3ZWJQcmVmZXJlbmNlczogewogICAgICBub2RlSW50ZWdyYXRpb246IHRydWUsCiAgICAgIGNvbnRleHRJc29sYXRpb246IGZhbHNlLAogICAgICB3ZWJ2aWV3VGFnOiB0cnVlLAogICAgICBiYWNrZ3JvdW5kVGhyb3R0bGluZzogZmFsc2UsCiAgICB9CiAgfSk7CgogIHdpbi5sb2FkRmlsZSgnaW5kZXguaHRtbCcpOwogIHdpbi5pc1Bpbm5lZCA9IGZhbHNlOwoKICB3aW4ub24oJ2JsdXInLCAoKSA9PiB7CiAgICBpZiAoIXdpbi5pc1Bpbm5lZCkgd2luLmhpZGUoKTsKICB9KTsKCiAgLy8gTmV2ZXIgYWN0dWFsbHkgY2xvc2Ug4oCUIGp1c3QgaGlkZQogIHdpbi5vbignY2xvc2UnLCAoZSkgPT4gewogICAgaWYgKCFhcHAuaXNRdWl0dGluZykgewogICAgICBlLnByZXZlbnREZWZhdWx0KCk7CiAgICAgIHdpbi5oaWRlKCk7CiAgICB9CiAgfSk7Cn0KCmZ1bmN0aW9uIHNob3dXaW5kb3coKSB7CiAgY29uc3QgeyBzY3JlZW4gfSA9IHJlcXVpcmUoJ2VsZWN0cm9uJyk7CiAgY29uc3QgeyB3aWR0aCwgaGVpZ2h0IH0gPSBzY3JlZW4uZ2V0UHJpbWFyeURpc3BsYXkoKS53b3JrQXJlYVNpemU7CiAgY29uc3QgdGIgPSB0cmF5LmdldEJvdW5kcygpOwoKICBsZXQgeCA9IE1hdGgucm91bmQodGIueCArIHRiLndpZHRoIC8gMiAtIFdJRFRIIC8gMik7CiAgbGV0IHkgPSB0Yi55ID4gaGVpZ2h0IC8gMiA/IHRiLnkgLSBIRUlHSFQgLSA0IDogdGIueSArIHRiLmhlaWdodCArIDQ7CiAgeCA9IE1hdGgubWF4KDAsIE1hdGgubWluKHgsIHdpZHRoIC0gV0lEVEgpKTsKICB5ID0gTWF0aC5tYXgoMCwgTWF0aC5taW4oeSwgaGVpZ2h0IC0gSEVJR0hUKSk7CgogIHdpbi5zZXRCb3VuZHMoeyB4LCB5LCB3aWR0aDogV0lEVEgsIGhlaWdodDogSEVJR0hUIH0pOwogIHdpbi5zaG93KCk7CiAgd2luLmZvY3VzKCk7Cn0KCmZ1bmN0aW9uIHRvZ2dsZVdpbmRvdygpIHsKICB3aW4uaXNWaXNpYmxlKCkgPyB3aW4uaGlkZSgpIDogc2hvd1dpbmRvdygpOwp9Cgpjb25zdCBQTEFZX0pTID0gYChmdW5jdGlvbigpewogIGNvbnN0IHYgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCd2aWRlbycpOwogIGlmICh2KSB7IHYucGF1c2VkID8gdi5wbGF5KCkgOiB2LnBhdXNlKCk7IHJldHVybiAhdi5wYXVzZWQ7IH0KICBkb2N1bWVudC5kaXNwYXRjaEV2ZW50KG5ldyBLZXlib2FyZEV2ZW50KCdrZXlkb3duJywgeyBrZXk6ICdrJywga2V5Q29kZTogNzUsIGJ1YmJsZXM6IHRydWUgfSkpOwogIHJldHVybiBudWxsOwp9KSgpYDsKCi8vIE5leHQgdHJhY2s6IGNsaWNrIFlUIE11c2ljIG5leHQgYnV0dG9uLCBmYWxsYmFjayBTaGlmdCtOCmNvbnN0IE5FWFRfSlMgPSBgKGZ1bmN0aW9uKCl7CiAgY29uc3QgYnRuID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcignW2RhdGEtdGVzdGlkPSJuZXh0LWJ1dHRvbiJdLCB5dG11c2ljLXBsYXllci1iYXIgI25leHQtYnV0dG9uJyk7CiAgaWYgKGJ0bikgeyBidG4uY2xpY2soKTsgcmV0dXJuIHRydWU7IH0KICBkb2N1bWVudC5kaXNwYXRjaEV2ZW50KG5ldyBLZXlib2FyZEV2ZW50KCdrZXlkb3duJywgeyBrZXk6ICdOJywgc2hpZnRLZXk6IHRydWUsIGtleUNvZGU6IDc4LCBidWJibGVzOiB0cnVlIH0pKTsKICByZXR1cm4gZmFsc2U7Cn0pKClgOwoKLy8gUmVzdGFydCB0cmFjayAob3IgcHJldiBpZiBhbHJlYWR5IGF0IHN0YXJ0KQpjb25zdCBSRVNUQVJUX0pTID0gYChmdW5jdGlvbigpewogIGNvbnN0IHYgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCd2aWRlbycpOwogIGlmICh2KSB7CiAgICBpZiAodi5jdXJyZW50VGltZSA+IDMpIHsgdi5jdXJyZW50VGltZSA9IDA7IHJldHVybiAncmVzdGFydGVkJzsgfQogICAgY29uc3QgYnRuID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcignW2RhdGEtdGVzdGlkPSJwcmV2LWJ1dHRvbiJdLCB5dG11c2ljLXBsYXllci1iYXIgI3ByZXYtYnV0dG9uJyk7CiAgICBpZiAoYnRuKSB7IGJ0bi5jbGljaygpOyByZXR1cm4gJ3ByZXYnOyB9CiAgICBkb2N1bWVudC5kaXNwYXRjaEV2ZW50KG5ldyBLZXlib2FyZEV2ZW50KCdrZXlkb3duJywgeyBrZXk6ICdQJywgc2hpZnRLZXk6IHRydWUsIGtleUNvZGU6IDgwLCBidWJibGVzOiB0cnVlIH0pKTsKICAgIHJldHVybiAncHJldi1zaG9ydGN1dCc7CiAgfQogIHJldHVybiBudWxsOwp9KSgpYDsKCmZ1bmN0aW9uIGdldEd1ZXN0KCkgewogIGlmICghd2luKSByZXR1cm4gbnVsbDsKICBjb25zdCB3aW5JZCA9IHdpbi53ZWJDb250ZW50cy5pZDsKICByZXR1cm4gd2ViQ29udGVudHMuZ2V0QWxsV2ViQ29udGVudHMoKQogICAgLmZpbmQod2MgPT4gd2MuaWQgIT09IHdpbklkICYmIHdjLmdldFR5cGUoKSA9PT0gJ3dlYnZpZXcnKSB8fCBudWxsOwp9CgpmdW5jdGlvbiB0b2dnbGVQbGF5UGF1c2UoKSB7IGNvbnN0IGcgPSBnZXRHdWVzdCgpOyBpZiAoZykgZy5leGVjdXRlSmF2YVNjcmlwdChQTEFZX0pTKS5jYXRjaCgoKSA9PiB7fSk7IH0KZnVuY3Rpb24gbmV4dFRyYWNrKCkgICAgICAgIHsgY29uc3QgZyA9IGdldEd1ZXN0KCk7IGlmIChnKSBnLmV4ZWN1dGVKYXZhU2NyaXB0KE5FWFRfSlMpLmNhdGNoKCgpID0+IHt9KTsgfQpmdW5jdGlvbiByZXN0YXJ0T3JQcmV2KCkgICAgeyBjb25zdCBnID0gZ2V0R3Vlc3QoKTsgaWYgKGcpIGcuZXhlY3V0ZUphdmFTY3JpcHQoUkVTVEFSVF9KUykuY2F0Y2goKCkgPT4ge30pOyB9CgpmdW5jdGlvbiBjcmVhdGVUcmF5KCkgewogIHRyeSB7CiAgICB0cmF5ID0gbmV3IFRyYXkocGF0aC5qb2luKF9fZGlybmFtZSwgJ2ljb24ucG5nJykpOwogIH0gY2F0Y2ggKGUpIHsKICAgIHRyYXkgPSBuZXcgVHJheShuYXRpdmVJbWFnZS5jcmVhdGVFbXB0eSgpKTsKICB9CiAgdHJheS5zZXRUb29sVGlwKCdZVHJheScpOwoKICBjb25zdCBtZW51ID0gTWVudS5idWlsZEZyb21UZW1wbGF0ZShbCiAgICB7IGxhYmVsOiAn4pa2L+KPuCAgUGxheSAvIFBhdXNlJywgIGFjY2VsZXJhdG9yOiAnQ3RybCtBbHQrU3BhY2UnLCBjbGljazogdG9nZ2xlUGxheVBhdXNlIH0sCiAgICB7IGxhYmVsOiAn4o+tICAgTmV4dCBUcmFjaycsICAgICAgIGFjY2VsZXJhdG9yOiAnQ3RybCtBbHQrUmlnaHQnLCBjbGljazogbmV4dFRyYWNrIH0sCiAgICB7IGxhYmVsOiAn4o+uICAgUmVzdGFydCAvIFByZXYnLCAgIGFjY2VsZXJhdG9yOiAnQ3RybCtBbHQrTGVmdCcsICBjbGljazogcmVzdGFydE9yUHJldiB9LAogICAgeyB0eXBlOiAnc2VwYXJhdG9yJyB9LAogICAgeyBsYWJlbDogJ/Cfk4wgUGluIFdpbmRvdycsIHR5cGU6ICdjaGVja2JveCcsIGNoZWNrZWQ6IGZhbHNlLAogICAgICBjbGljazogKGl0ZW0pID0+IHsgd2luLmlzUGlubmVkID0gaXRlbS5jaGVja2VkOyBpZiAoaXRlbS5jaGVja2VkKSBzaG93V2luZG93KCk7IH0KICAgIH0sCiAgICB7IHR5cGU6ICdzZXBhcmF0b3InIH0sCiAgICB7IGxhYmVsOiAn8J+OtSBZb3VUdWJlIE11c2ljJywgY2xpY2s6ICgpID0+IHsgd2luLndlYkNvbnRlbnRzLnNlbmQoJ25hdmlnYXRlJywgJ2h0dHBzOi8vbXVzaWMueW91dHViZS5jb20nKTsgc2hvd1dpbmRvdygpOyB9IH0sCiAgICB7IGxhYmVsOiAn8J+TuiBZb3VUdWJlJywgICAgICAgY2xpY2s6ICgpID0+IHsgd2luLndlYkNvbnRlbnRzLnNlbmQoJ25hdmlnYXRlJywgJ2h0dHBzOi8vd3d3LnlvdXR1YmUuY29tJyk7ICAgc2hvd1dpbmRvdygpOyB9IH0sCiAgICB7IHR5cGU6ICdzZXBhcmF0b3InIH0sCiAgICB7IGxhYmVsOiAnUXVpdCcsIGNsaWNrOiAoKSA9PiB7IGFwcC5pc1F1aXR0aW5nID0gdHJ1ZTsgYXBwLnF1aXQoKTsgfSB9CiAgXSk7CgogIHRyYXkuc2V0Q29udGV4dE1lbnUobWVudSk7CiAgdHJheS5vbignY2xpY2snLCB0b2dnbGVXaW5kb3cpOwogIHRyYXkub24oJ2RvdWJsZS1jbGljaycsIHRvZ2dsZVdpbmRvdyk7Cn0KCmNvbnN0IHsgaXBjTWFpbiB9ID0gcmVxdWlyZSgnZWxlY3Ryb24nKTsKaXBjTWFpbi5vbigncGluLWNoYW5nZWQnLCAoZSwgcGlubmVkKSA9PiB7IGlmICh3aW4pIHdpbi5pc1Bpbm5lZCA9IHBpbm5lZDsgfSk7CgphcHAud2hlblJlYWR5KCkudGhlbigoKSA9PiB7CiAgYXBwLnNldEFwcFVzZXJNb2RlbElkKCdjb20ueXRyYXkuYXBwJyk7CiAgaWYgKHByb2Nlc3MucGxhdGZvcm0gPT09ICdkYXJ3aW4nKSBhcHAuZG9jay5oaWRlKCk7CgogIGNyZWF0ZVdpbmRvdygpOwogIGNyZWF0ZVRyYXkoKTsKCiAgY29uc3Qgc2hvcnRjdXRzID0gWwogICAgW1NIT1JUQ1VULCAgICAgICAgICAgICAgICAgICAgICAgdG9nZ2xlUGxheVBhdXNlLCAnUGxheS9QYXVzZSddLAogICAgWydDb21tYW5kT3JDb250cm9sK0FsdCtSaWdodCcsICAgbmV4dFRyYWNrLCAgICAgICAnTmV4dCB0cmFjayddLAogICAgWydDb21tYW5kT3JDb250cm9sK0FsdCtMZWZ0JywgICAgcmVzdGFydE9yUHJldiwgICAnUmVzdGFydC9QcmV2J10sCiAgXTsKICBmb3IgKGNvbnN0IFtjb21ibywgZm4sIGxhYmVsXSBvZiBzaG9ydGN1dHMpIHsKICAgIGNvbnN0IG9rID0gZ2xvYmFsU2hvcnRjdXQucmVnaXN0ZXIoY29tYm8sIGZuKTsKICAgIGlmICghb2spIGNvbnNvbGUud2FybihgU2hvcnRjdXQgZmFpbGVkIHRvIHJlZ2lzdGVyOiAke2xhYmVsfSAoJHtjb21ib30pYCk7CiAgfQp9KTsKCmFwcC5vbignYmVmb3JlLXF1aXQnLCAoKSA9PiB7IGFwcC5pc1F1aXR0aW5nID0gdHJ1ZTsgfSk7CmFwcC5vbignd2lsbC1xdWl0JywgKCkgPT4gZ2xvYmFsU2hvcnRjdXQudW5yZWdpc3RlckFsbCgpKTsKYXBwLm9uKCd3aW5kb3ctYWxsLWNsb3NlZCcsIChlKSA9PiB7IGlmICghYXBwLmlzUXVpdHRpbmcpIGUucHJldmVudERlZmF1bHQoKTsgfSk7Cg==",
    "index.html": "PCFET0NUWVBFIGh0bWw+CjxodG1sPgo8aGVhZD4KICA8bWV0YSBjaGFyc2V0PSJVVEYtOCI+CiAgPHRpdGxlPllUcmF5PC90aXRsZT4KICA8c3R5bGU+CiAgICAqIHsgbWFyZ2luOiAwOyBwYWRkaW5nOiAwOyBib3gtc2l6aW5nOiBib3JkZXItYm94OyB9CiAgICBib2R5IHsKICAgICAgYmFja2dyb3VuZDogIzBmMGYwZjsKICAgICAgZm9udC1mYW1pbHk6IC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgc2Fucy1zZXJpZjsKICAgICAgZGlzcGxheTogZmxleDsKICAgICAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjsKICAgICAgaGVpZ2h0OiAxMDB2aDsKICAgICAgb3ZlcmZsb3c6IGhpZGRlbjsKICAgICAgYm9yZGVyOiAxcHggc29saWQgIzJhMmEyYTsKICAgICAgYm9yZGVyLXJhZGl1czogOHB4OwogICAgfQogICAgI3RpdGxlYmFyIHsKICAgICAgLXdlYmtpdC1hcHAtcmVnaW9uOiBkcmFnOwogICAgICBiYWNrZ3JvdW5kOiAjMTYxNjE2OwogICAgICBwYWRkaW5nOiA3cHggMTBweDsKICAgICAgZGlzcGxheTogZmxleDsKICAgICAgYWxpZ24taXRlbXM6IGNlbnRlcjsKICAgICAgZ2FwOiA2cHg7CiAgICAgIGZsZXgtc2hyaW5rOiAwOwogICAgICBib3JkZXItYm90dG9tOiAxcHggc29saWQgIzJhMmEyYTsKICAgICAgYm9yZGVyLXJhZGl1czogOHB4IDhweCAwIDA7CiAgICB9CiAgICAuZG90IHsgd2lkdGg6MTBweDsgaGVpZ2h0OjEwcHg7IGJvcmRlci1yYWRpdXM6NTAlOyBiYWNrZ3JvdW5kOiNmZjQ0NDQ7IGZsZXgtc2hyaW5rOjA7IH0KICAgICN1cmwtYmFyIHsKICAgICAgZmxleDogMTsKICAgICAgYmFja2dyb3VuZDogIzBhMGEwYTsKICAgICAgYm9yZGVyOiAxcHggc29saWQgIzJhMmEyYTsKICAgICAgYm9yZGVyLXJhZGl1czogNHB4OwogICAgICBjb2xvcjogI2NjYzsKICAgICAgZm9udC1zaXplOiAxMXB4OwogICAgICBwYWRkaW5nOiA0cHggOHB4OwogICAgICBvdXRsaW5lOiBub25lOwogICAgICAtd2Via2l0LWFwcC1yZWdpb246IG5vLWRyYWc7CiAgICB9CiAgICAjdXJsLWJhcjpmb2N1cyB7IGJvcmRlci1jb2xvcjogI2ZmNDQ0NDsgfQogICAgLmJ0biB7CiAgICAgIC13ZWJraXQtYXBwLXJlZ2lvbjogbm8tZHJhZzsKICAgICAgYmFja2dyb3VuZDogIzFlMWUxZTsKICAgICAgYm9yZGVyOiAxcHggc29saWQgIzMzMzsKICAgICAgY29sb3I6ICNhYWE7CiAgICAgIGN1cnNvcjogcG9pbnRlcjsKICAgICAgZm9udC1zaXplOiAxMnB4OwogICAgICBwYWRkaW5nOiAzcHggN3B4OwogICAgICBib3JkZXItcmFkaXVzOiA0cHg7CiAgICAgIHRyYW5zaXRpb246IGFsbCAwLjFzOwogICAgICBmbGV4LXNocmluazogMDsKICAgIH0KICAgIC5idG46aG92ZXIgeyBjb2xvcjojZmZmOyBiYWNrZ3JvdW5kOiMyYTJhMmE7IGJvcmRlci1jb2xvcjojNTU1OyB9CiAgICAuYnRuLmFjdGl2ZSB7IGNvbG9yOiNmZjQ0NDQ7IGJvcmRlci1jb2xvcjojZmY0NDQ0OyB9CiAgICAjaGludCB7CiAgICAgIGJhY2tncm91bmQ6ICMxMTE7CiAgICAgIGJvcmRlci1ib3R0b206IDFweCBzb2xpZCAjMWUxZTFlOwogICAgICBwYWRkaW5nOiAzcHggMTBweDsKICAgICAgZm9udC1zaXplOiAxMHB4OwogICAgICBjb2xvcjogIzNhM2EzYTsKICAgICAgZGlzcGxheTogZmxleDsKICAgICAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuOwogICAgICBhbGlnbi1pdGVtczogY2VudGVyOwogICAgICBmbGV4LXNocmluazogMDsKICAgIH0KICAgIGtiZCB7CiAgICAgIGJhY2tncm91bmQ6ICMxZTFlMWU7CiAgICAgIGJvcmRlcjogMXB4IHNvbGlkICMzMzM7CiAgICAgIGJvcmRlci1yYWRpdXM6IDNweDsKICAgICAgcGFkZGluZzogMCA0cHg7CiAgICAgIGZvbnQtc2l6ZTogOXB4OwogICAgICBjb2xvcjogIzU1NTsKICAgIH0KICAgICN3di13cmFwIHsKICAgICAgZmxleDogMTsKICAgICAgcG9zaXRpb246IHJlbGF0aXZlOwogICAgICBvdmVyZmxvdzogaGlkZGVuOwogICAgICBib3JkZXItcmFkaXVzOiAwIDAgOHB4IDhweDsKICAgIH0KICAgIHdlYnZpZXcgewogICAgICB3aWR0aDogMTAwJTsKICAgICAgaGVpZ2h0OiAxMDAlOwogICAgICBkaXNwbGF5OiBmbGV4OwogICAgfQogICAgI2JhciB7CiAgICAgIHBvc2l0aW9uOiBhYnNvbHV0ZTsKICAgICAgdG9wOiAwOyBsZWZ0OiAwOyByaWdodDogMDsKICAgICAgaGVpZ2h0OiAycHg7CiAgICAgIGJhY2tncm91bmQ6ICNmZjQ0NDQ7CiAgICAgIHRyYW5zZm9ybS1vcmlnaW46IGxlZnQ7CiAgICAgIHRyYW5zZm9ybTogc2NhbGVYKDApOwogICAgICB6LWluZGV4OiAxMDsKICAgICAgdHJhbnNpdGlvbjogb3BhY2l0eSAwLjNzOwogICAgfQogICAgI2Jhci5sb2FkaW5nIHsgYW5pbWF0aW9uOiBsb2FkIDEuOHMgZWFzZSBpbmZpbml0ZTsgfQogICAgQGtleWZyYW1lcyBsb2FkIHsKICAgICAgMCUgICB7IHRyYW5zZm9ybTogc2NhbGVYKDApOyAgIG9wYWNpdHk6IDE7IH0KICAgICAgNjAlICB7IHRyYW5zZm9ybTogc2NhbGVYKDAuOCk7IG9wYWNpdHk6IDE7IH0KICAgICAgMTAwJSB7IHRyYW5zZm9ybTogc2NhbGVYKDEpOyAgIG9wYWNpdHk6IDA7IH0KICAgIH0KICA8L3N0eWxlPgo8L2hlYWQ+Cjxib2R5PgogIDxkaXYgaWQ9InRpdGxlYmFyIj4KICAgIDxkaXYgY2xhc3M9ImRvdCI+PC9kaXY+CiAgICA8aW5wdXQgaWQ9InVybC1iYXIiIHR5cGU9InRleHQiIHZhbHVlPSJodHRwczovL211c2ljLnlvdXR1YmUuY29tIiBzcGVsbGNoZWNrPSJmYWxzZSIgLz4KICAgIDxidXR0b24gY2xhc3M9ImJ0biIgaWQ9ImJ0bi1iYWNrIiAgIHRpdGxlPSJCYWNrIj7il4A8L2J1dHRvbj4KICAgIDxidXR0b24gY2xhc3M9ImJ0biIgaWQ9ImJ0bi1md2QiICAgIHRpdGxlPSJGb3J3YXJkIj7ilrY8L2J1dHRvbj4KICAgIDxidXR0b24gY2xhc3M9ImJ0biIgaWQ9ImJ0bi1yZWxvYWQiIHRpdGxlPSJSZWxvYWQiPuKGujwvYnV0dG9uPgogICAgPGJ1dHRvbiBjbGFzcz0iYnRuIiBpZD0iYnRuLXBsYXkiICAgdGl0bGU9IlBsYXkvUGF1c2UiPuKPrzwvYnV0dG9uPgogICAgPGJ1dHRvbiBjbGFzcz0iYnRuIiBpZD0iYnRuLXBpbiIgICAgdGl0bGU9IlBpbiB3aW5kb3ciPvCfk4w8L2J1dHRvbj4KICA8L2Rpdj4KICA8ZGl2IGlkPSJoaW50Ij4KICAgIDxzcGFuPuKPryA8a2JkPkN0cmwrQWx0K1NwYWNlPC9rYmQ+ICZuYnNwOyDij60gPGtiZD5DdHJsK0FsdCvihpI8L2tiZD4gJm5ic3A7IOKPriA8a2JkPkN0cmwrQWx0K+KGkDwva2JkPjwvc3Bhbj4KICAgIDxzcGFuIGlkPSJzdGF0dXMiPuKPuDwvc3Bhbj4KICA8L2Rpdj4KICA8ZGl2IGlkPSJ3di13cmFwIj4KICAgIDxkaXYgaWQ9ImJhciI+PC9kaXY+CiAgICA8d2VidmlldyBpZD0id3YiCiAgICAgIHNyYz0iaHR0cHM6Ly9tdXNpYy55b3V0dWJlLmNvbSIKICAgICAgcGFydGl0aW9uPSJwZXJzaXN0Onl0cmF5IgogICAgICBhbGxvd3BvcHVwcz0iZmFsc2UiCiAgICAgIHVzZXJhZ2VudD0iTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjAuMCBTYWZhcmkvNTM3LjM2Ij4KICAgIDwvd2Vidmlldz4KICA8L2Rpdj4KCiAgPHNjcmlwdD4KICAgIGNvbnN0IHsgaXBjUmVuZGVyZXIgfSA9IHJlcXVpcmUoJ2VsZWN0cm9uJyk7CiAgICBjb25zdCB3diAgICAgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnd3YnKTsKICAgIGNvbnN0IHVybEJhciA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCd1cmwtYmFyJyk7CiAgICBjb25zdCBiYXIgICAgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnYmFyJyk7CiAgICBjb25zdCBzdGF0dXMgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnc3RhdHVzJyk7CiAgICBjb25zdCBidG5QaW4gPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnYnRuLXBpbicpOwogICAgbGV0IHBpbm5lZCA9IGZhbHNlOwoKICAgIC8vIOKUgOKUgCBOYXZpZ2F0aW9uIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgAogICAgdXJsQmFyLmFkZEV2ZW50TGlzdGVuZXIoJ2tleWRvd24nLCBlID0+IHsKICAgICAgaWYgKGUua2V5ICE9PSAnRW50ZXInKSByZXR1cm47CiAgICAgIGxldCB1cmwgPSB1cmxCYXIudmFsdWUudHJpbSgpOwogICAgICBpZiAoIXVybC5zdGFydHNXaXRoKCdodHRwJykpIHVybCA9ICdodHRwczovLycgKyB1cmw7CiAgICAgIHd2LnNyYyA9IHVybDsKICAgIH0pOwoKICAgIHd2LmFkZEV2ZW50TGlzdGVuZXIoJ2RpZC1uYXZpZ2F0ZScsICAgICAgICAgZSA9PiB1cmxCYXIudmFsdWUgPSBlLnVybCk7CiAgICB3di5hZGRFdmVudExpc3RlbmVyKCdkaWQtbmF2aWdhdGUtaW4tcGFnZScsIGUgPT4gdXJsQmFyLnZhbHVlID0gZS51cmwpOwogICAgd3YuYWRkRXZlbnRMaXN0ZW5lcignZGlkLXN0YXJ0LWxvYWRpbmcnLCAgICAoKSA9PiBiYXIuY2xhc3NMaXN0LmFkZCgnbG9hZGluZycpKTsKICAgIHd2LmFkZEV2ZW50TGlzdGVuZXIoJ2RpZC1zdG9wLWxvYWRpbmcnLCAgICAgKCkgPT4gYmFyLmNsYXNzTGlzdC5yZW1vdmUoJ2xvYWRpbmcnKSk7CgogICAgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2J0bi1iYWNrJykub25jbGljayAgID0gKCkgPT4gd3YuZ29CYWNrKCk7CiAgICBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnYnRuLWZ3ZCcpLm9uY2xpY2sgICAgPSAoKSA9PiB3di5nb0ZvcndhcmQoKTsKICAgIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdidG4tcmVsb2FkJykub25jbGljayA9ICgpID0+IHd2LnJlbG9hZCgpOwoKICAgIC8vIOKUgOKUgCBQbGF5L1BhdXNlIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgAogICAgY29uc3QgUExBWV9KUyA9IGAoZnVuY3Rpb24oKXsKICAgICAgY29uc3QgdiA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoJ3ZpZGVvJyk7CiAgICAgIGlmICh2KSB7IHYucGF1c2VkID8gdi5wbGF5KCkgOiB2LnBhdXNlKCk7IHJldHVybiAhdi5wYXVzZWQ7IH0KICAgICAgZG9jdW1lbnQuZGlzcGF0Y2hFdmVudChuZXcgS2V5Ym9hcmRFdmVudCgna2V5ZG93bicseyBrZXk6J2snLCBrZXlDb2RlOjc1LCBidWJibGVzOnRydWUgfSkpOwogICAgICByZXR1cm4gbnVsbDsKICAgIH0pKClgOwoKICAgIGZ1bmN0aW9uIHRvZ2dsZVBsYXkoKSB7CiAgICAgIHd2LmV4ZWN1dGVKYXZhU2NyaXB0KFBMQVlfSlMpCiAgICAgICAgLnRoZW4ocCA9PiB7IGlmIChwICE9PSBudWxsKSBzdGF0dXMudGV4dENvbnRlbnQgPSBwID8gJ+KWticgOiAn4o+4JzsgfSkKICAgICAgICAuY2F0Y2goKCkgPT4ge30pOwogICAgfQoKICAgIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdidG4tcGxheScpLm9uY2xpY2sgPSB0b2dnbGVQbGF5OwogICAgaXBjUmVuZGVyZXIub24oJ3RvZ2dsZS1wbGF5JywgdG9nZ2xlUGxheSk7CgogICAgLy8g4pSA4pSAIFBpbiDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKICAgIGJ0blBpbi5vbmNsaWNrID0gKCkgPT4gewogICAgICBwaW5uZWQgPSAhcGlubmVkOwogICAgICBidG5QaW4uY2xhc3NMaXN0LnRvZ2dsZSgnYWN0aXZlJywgcGlubmVkKTsKICAgICAgaXBjUmVuZGVyZXIuc2VuZCgncGluLWNoYW5nZWQnLCBwaW5uZWQpOwogICAgfTsKCiAgICAvLyDilIDilIAgTmF2aWdhdGUgZnJvbSB0cmF5IG1lbnUg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACiAgICBpcGNSZW5kZXJlci5vbignbmF2aWdhdGUnLCAoZSwgdXJsKSA9PiB7CiAgICAgIHd2LnNyYyA9IHVybDsKICAgICAgdXJsQmFyLnZhbHVlID0gdXJsOwogICAgfSk7CgogICAgLy8g4pSA4pSAIFBvbGwgcGxheSBzdGF0ZSBldmVyeSAzcyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKICAgIHNldEludGVydmFsKCgpID0+IHsKICAgICAgd3YuZXhlY3V0ZUphdmFTY3JpcHQoJygoKT0+eyBjb25zdCB2PWRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoInZpZGVvIik7IHJldHVybiB2PyF2LnBhdXNlZDpudWxsOyB9KSgpJykKICAgICAgICAudGhlbihwID0+IHsgaWYgKHAgIT09IG51bGwpIHN0YXR1cy50ZXh0Q29udGVudCA9IHAgPyAn4pa2JyA6ICfij7gnOyB9KQogICAgICAgIC5jYXRjaCgoKSA9PiB7fSk7CiAgICB9LCAzMDAwKTsKICA8L3NjcmlwdD4KPC9ib2R5Pgo8L2h0bWw+Cg==",
    "icon.png": "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",
    "package.json": "ewogICJuYW1lIjogInl0cmF5IiwKICAidmVyc2lvbiI6ICIxLjMuMCIsCiAgImRlc2NyaXB0aW9uIjogIkxpZ2h0d2VpZ2h0IFlvdVR1YmUgdHJheSBwbGF5ZXIiLAogICJtYWluIjogIm1haW4uanMiLAogICJzY3JpcHRzIjogewogICAgInN0YXJ0IjogImVsZWN0cm9uIC4iCiAgfSwKICAiZGV2RGVwZW5kZW5jaWVzIjogewogICAgImVsZWN0cm9uIjogIl4yOC4wLjAiCiAgfQp9",
    "README.md": "IyBZVHJheQoKQSBsaWdodHdlaWdodCBZb3VUdWJlL1lvdVR1YmUgTXVzaWMgcGxheWVyIHRoYXQgbGl2ZXMgaW4gdGhlIFdpbmRvd3Mgc3lzdGVtIHRyYXkuCgojIyBGZWF0dXJlcwoKLSBTaXRzIGluIHRoZSAqKnN5c3RlbSB0cmF5Kiog4oCUIG5vIHRhc2tiYXIgY2x1dHRlcgotIENvbXBhY3QgYnJvd3NlciB3aW5kb3cgcG9wcyB1cCBvbiB0cmF5IGNsaWNrCi0gKipHbG9iYWwgc2hvcnRjdXRzKiogd29yayBldmVuIHdoZW4gbWluaW1pc2VkOgogIC0gYEN0cmwrQWx0K1NwYWNlYCDigJQgUGxheSAvIFBhdXNlCiAgLSBgQ3RybCtBbHQr4oaSYCDigJQgTmV4dCB0cmFjawogIC0gYEN0cmwrQWx0K+KGkGAg4oCUIFJlc3RhcnQgdHJhY2sgKG9yIHByZXZpb3VzIGlmIGFscmVhZHkgYXQgc3RhcnQpCi0gUGVyc2lzdGVudCBsb2dpbiDigJQgWW91VHViZSBzZXNzaW9uIGlzIHJlbWVtYmVyZWQgYmV0d2VlbiBsYXVuY2hlcwotIFBpbiBtb2RlIHRvIGtlZXAgdGhlIHdpbmRvdyB2aXNpYmxlCi0gV29ya3Mgd2l0aCBZb3VUdWJlIE11c2ljIGFuZCByZWd1bGFyIFlvdVR1YmUKCiMjIFJlcXVpcmVtZW50cwoKLSBXaW5kb3dzIDEwLzExCi0gTm9kZS5qcyB2MTgrIGFuZCBucG0g4oCUIGh0dHBzOi8vbm9kZWpzLm9yZwoKIyMgUXVpY2sgc3RhcnQgKGRldikKCmBgYGJhc2gKbnBtIGluc3RhbGwKbnBtIHN0YXJ0CmBgYAoKIyMgQnVpbGQgcG9ydGFibGUgLmV4ZQoKYGBgYmFzaApweXRob24gZGVwbG95X1lUcmF5LnB5CmBgYAoKT3V0cHV0OiBgWVRyYXktPHZlcnNpb24+LmV4ZWAgaW4gdGhlIHNhbWUgZm9sZGVyIGFzIHRoZSBzY3JpcHQuIEJ1aWxkIGZvbGRlciBpcyBhdXRvbWF0aWNhbGx5IGNsZWFuZWQgdXAuCgojIyBTaG9ydGN1dHMKCnwgU2hvcnRjdXQgfCBBY3Rpb24gfAp8LS0tfC0tLXwKfCBgQ3RybCtBbHQrU3BhY2VgIHwgUGxheSAvIFBhdXNlIHwKfCBgQ3RybCtBbHQr4oaSYCB8IE5leHQgdHJhY2sgfAp8IGBDdHJsK0FsdCvihpBgIHwgUmVzdGFydCAvIFByZXZpb3VzIHRyYWNrIHwKCiMjIFZlcnNpb24gaGlzdG9yeQoKfCBWZXJzaW9uIHwgQ2hhbmdlcyB8CnwtLS18LS0tfAp8IDEuMy4wIHwgR2xvYmFsIHNob3J0Y3V0cyBmaXhlZCAoQ2hyb21pdW0gdGhyb3R0bGUgZmxhZ3MpLCBuZXh0L3Jlc3RhcnQgc2hvcnRjdXRzIGFkZGVkIHwKfCAxLjIuMCB8IEJhY2tncm91bmQgdGhyb3R0bGluZyBmaXggYXR0ZW1wdCAoYmcvcG9wdXAgc3BsaXQg4oCUIHJldmVydGVkKSB8CnwgMS4xLjAgfCBGaXhlZCBtYWxmb3JtZWQgUE5HIGljb24gfAp8IDEuMC4wIHwgSW5pdGlhbCByZWxlYXNlIHwK",
    "LICENSE": "TUlUIExpY2Vuc2UKCkNvcHlyaWdodCAoYykgMjAyNSBHcmFudCBSb2dlcnMKClBlcm1pc3Npb24gaXMgaGVyZWJ5IGdyYW50ZWQsIGZyZWUgb2YgY2hhcmdlLCB0byBhbnkgcGVyc29uIG9idGFpbmluZyBhIGNvcHkKb2YgdGhpcyBzb2Z0d2FyZSBhbmQgYXNzb2NpYXRlZCBkb2N1bWVudGF0aW9uIGZpbGVzICh0aGUgIlNvZnR3YXJlIiksIHRvIGRlYWwKaW4gdGhlIFNvZnR3YXJlIHdpdGhvdXQgcmVzdHJpY3Rpb24sIGluY2x1ZGluZyB3aXRob3V0IGxpbWl0YXRpb24gdGhlIHJpZ2h0cwp0byB1c2UsIGNvcHksIG1vZGlmeSwgbWVyZ2UsIHB1Ymxpc2gsIGRpc3RyaWJ1dGUsIHN1YmxpY2Vuc2UsIGFuZC9vciBzZWxsCmNvcGllcyBvZiB0aGUgU29mdHdhcmUsIGFuZCB0byBwZXJtaXQgcGVyc29ucyB0byB3aG9tIHRoZSBTb2Z0d2FyZSBpcwpmdXJuaXNoZWQgdG8gZG8gc28sIHN1YmplY3QgdG8gdGhlIGZvbGxvd2luZyBjb25kaXRpb25zOgoKVGhlIGFib3ZlIGNvcHlyaWdodCBub3RpY2UgYW5kIHRoaXMgcGVybWlzc2lvbiBub3RpY2Ugc2hhbGwgYmUgaW5jbHVkZWQgaW4gYWxsCmNvcGllcyBvciBzdWJzdGFudGlhbCBwb3J0aW9ucyBvZiB0aGUgU29mdHdhcmUuCgpUSEUgU09GVFdBUkUgSVMgUFJPVklERUQgIkFTIElTIiwgV0lUSE9VVCBXQVJSQU5UWSBPRiBBTlkgS0lORCwgRVhQUkVTUyBPUgpJTVBMSUVELCBJTkNMVURJTkcgQlVUIE5PVCBMSU1JVEVEIFRPIFRIRSBXQVJSQU5USUVTIE9GIE1FUkNIQU5UQUJJTElUWSwKRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSIFBVUlBPU0UgQU5EIE5PTklORlJJTkdFTUVOVC4gSU4gTk8gRVZFTlQgU0hBTEwgVEhFCkFVVEhPUlMgT1IgQ09QWVJJR0hUIEhPTERFUlMgQkUgTElBQkxFIEZPUiBBTlkgQ0xBSU0sIERBTUFHRVMgT1IgT1RIRVIKTElBQklMSVRZLCBXSEVUSEVSIElOIEFOIEFDVElPTiBPRiBDT05UUkFDVCwgVE9SVCBPUiBPVEhFUldJU0UsIEFSSVNJTkcgRlJPTSwKT1VUIE9GIE9SIElOIENPTk5FQ1RJT04gV0lUSCBUSEUgU09GVFdBUkUgT1IgVEhFIFVTRSBPUiBPVEhFUiBERUFMSU5HUyBJTiBUSEUKU09GVFdBUkUuCg==",
    ".gitignore": "bm9kZV9tb2R1bGVzLwpkaXN0LwpfeXRyYXlfYnVpbGQvCioubG9nCi5EU19TdG9yZQpUaHVtYnMuZGIK",
    "AGENTS.md": "IyBZVHJheSDigJQgQWdlbnQgSW5zdHJ1Y3Rpb25zCgpUaGlzIGZpbGUgdGVsbHMgQ2xhdWRlIChvciBhbnkgQUkgYWdlbnQpIGV2ZXJ5dGhpbmcgbmVlZGVkIHRvIHdvcmsgb24gYW5kIGRlcGxveSB0aGlzIHByb2plY3QgYXV0b25vbW91c2x5LgoKIyMgV2hhdCB0aGlzIHByb2plY3QgaXMKCllUcmF5IGlzIGEgbGlnaHR3ZWlnaHQgRWxlY3Ryb24gYXBwIHRoYXQgcnVucyBpbiB0aGUgV2luZG93cyBzeXN0ZW0gdHJheSBhbmQgcGxheXMgWW91VHViZSAvIFlvdVR1YmUgTXVzaWMuIEl0IHVzZXMgYSBzaW5nbGUgYEJyb3dzZXJXaW5kb3dgIGNvbnRhaW5pbmcgYSBgPHdlYnZpZXc+YCB0YWcuIEdsb2JhbCBzaG9ydGN1dHMgYXJlIHJlZ2lzdGVyZWQgdmlhIEVsZWN0cm9uJ3MgYGdsb2JhbFNob3J0Y3V0YCBBUEkgYW5kIGV4ZWN1dGUgSmF2YVNjcmlwdCBkaXJlY3RseSBpbnRvIHRoZSB3ZWJ2aWV3J3MgZ3Vlc3QgYHdlYkNvbnRlbnRzYC4KCiMjIFJlcG8gc3RydWN0dXJlCgpgYGAKWVRyYXkvCuKUnOKUgOKUgCBtYWluLmpzICAgICAgICAgICMgRWxlY3Ryb24gbWFpbiBwcm9jZXNzIOKAlCB0cmF5LCB3aW5kb3csIHNob3J0Y3V0cwrilJzilIDilIAgaW5kZXguaHRtbCAgICAgICAjIFJlbmRlcmVyIOKAlCB3ZWJ2aWV3ICsgVUkgY2hyb21lCuKUnOKUgOKUgCBpY29uLnBuZyAgICAgICAgICMgMjU2eDI1NiBSR0JBIFBORyB0cmF5IGljb24gKGdlbmVyYXRlZCB2aWEgUGlsbG93KQrilJzilIDilIAgcGFja2FnZS5qc29uICAgICAjIG5wbSBtYW5pZmVzdCDigJQgdmVyc2lvbiBsaXZlcyBoZXJlCuKUnOKUgOKUgCBkZXBsb3lfWVRyYXkucHkgICMgU2VsZi1jb250YWluZWQgb25lLWNsaWNrIGJ1aWxkZXIgKHNlZSBiZWxvdykK4pSc4pSA4pSAIFJFQURNRS5tZCAgICAgICAgIyBVc2VyLWZhY2luZyBkb2NzCuKUnOKUgOKUgCBMSUNFTlNFICAgICAgICAgICMgTUlUCuKUnOKUgOKUgCAuZ2l0aWdub3JlCuKUlOKUgOKUgCBBR0VOVFMubWQgICAgICAgICMgVGhpcyBmaWxlCmBgYAoKIyMgS2V5IGFyY2hpdGVjdHVyZSBkZWNpc2lvbnMKCi0gKipTaW5nbGUgd2luZG93Kiog4oCUIHRoZSB3ZWJ2aWV3IGxpdmVzIGluc2lkZSB0aGUgcG9wdXAgd2luZG93LCBub3QgYSBzZXBhcmF0ZSBiYWNrZ3JvdW5kIHdpbmRvdy4gQmFja2dyb3VuZCB0aHJvdHRsaW5nIGlzIHByZXZlbnRlZCB2aWEgdGhyZWUgQ2hyb21pdW0gY29tbWFuZC1saW5lIGZsYWdzIGluIGBtYWluLmpzYCAobGluZXMgNC03KS4gRG8gbm90IHJldmVydCB0byBhIHR3by13aW5kb3cgYXJjaGl0ZWN0dXJlLgotICoqR2xvYmFsIHNob3J0Y3V0cyDihpIgZ3Vlc3Qgd2ViQ29udGVudHMqKiDigJQgYHdlYkNvbnRlbnRzLmdldEFsbFdlYkNvbnRlbnRzKClgIGZpbmRzIHRoZSB3ZWJ2aWV3J3MgZ3Vlc3QgcHJvY2VzcyBieSB0eXBlLiBKUyBpcyBleGVjdXRlZCB0aGVyZSBkaXJlY3RseSwgbm90IHZpYSBJUEMgdG8gdGhlIHJlbmRlcmVyLgotICoqYmFja2dyb3VuZFRocm90dGxpbmc6IGZhbHNlKiogb24gdGhlIEJyb3dzZXJXaW5kb3cgcGx1cyB0aGUgYXBwLWxldmVsIHN3aXRjaGVzIGFyZSBib3RoIHJlcXVpcmVkLiBSZW1vdmUgZWl0aGVyIGFuZCBzaG9ydGN1dHMgc3RvcCB3b3JraW5nIHdoZW4gbWluaW1pc2VkLgotICoqUGVyc2lzdGVudCBzZXNzaW9uKiog4oCUIHRoZSB3ZWJ2aWV3IHVzZXMgYHBhcnRpdGlvbj0icGVyc2lzdDp5dHJheSJgIHNvIFlvdVR1YmUgbG9naW4gc3Vydml2ZXMgcmVzdGFydHMuCgojIyBWZXJzaW9uaW5nIHJ1bGVzCgotIFZlcnNpb24gaXMgc3RvcmVkIGluIGBwYWNrYWdlLmpzb25gIOKGkiBgInZlcnNpb24iYAotIEluY3JlbWVudCB0aGUgKiptaW5vcioqIHZlcnNpb24gKGAxLnguMGApIGZvciBldmVyeSBtZWFuaW5nZnVsIGNoYW5nZQotIEN1cnJlbnQgdmVyc2lvbiBhdCBsYXN0IGVkaXQ6ICoqMS4zLjAqKgotIEFmdGVyIGVkaXRpbmcgYW55IHNvdXJjZSBmaWxlLCByZS1lbWJlZCBpbnRvIGBkZXBsb3lfWVRyYXkucHlgIChzZWUgYmVsb3cpCgojIyBIb3cgdG8gbWFrZSBjaGFuZ2VzCgoxLiBFZGl0IHRoZSByZWxldmFudCBzb3VyY2UgZmlsZSAoYG1haW4uanNgLCBgaW5kZXguaHRtbGAsIGV0Yy4pCjIuIEJ1bXAgdGhlIG1pbm9yIHZlcnNpb24gaW4gYHBhY2thZ2UuanNvbmAKMy4gUmUtcnVuIHRoZSBlbWJlZCBzdGVwIHRvIGJha2UgdXBkYXRlZCBmaWxlcyBpbnRvIGBkZXBsb3lfWVRyYXkucHlgOgoKYGBgcHl0aG9uCiMgUmUtZW1iZWQgYWxsIHNvdXJjZSBmaWxlcyBpbnRvIGRlcGxveV9ZVHJheS5weQppbXBvcnQgYmFzZTY0LCBqc29uLCByZQpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKCmZpbGVzX3RvX2VtYmVkID0gWydtYWluLmpzJywgJ2luZGV4Lmh0bWwnLCAnaWNvbi5wbmcnLCAncGFja2FnZS5qc29uJywKICAgICAgICAgICAgICAgICAgJ1JFQURNRS5tZCcsICdMSUNFTlNFJywgJy5naXRpZ25vcmUnLCAnQUdFTlRTLm1kJ10KZW1iZWRkZWQgPSB7fQpmb3IgZiBpbiBmaWxlc190b19lbWJlZDoKICAgIHdpdGggb3BlbihmLCAncmInKSBhcyBmaDoKICAgICAgICBlbWJlZGRlZFtmXSA9IGJhc2U2NC5iNjRlbmNvZGUoZmgucmVhZCgpKS5kZWNvZGUoKQoKZGVwbG95ID0gUGF0aCgnZGVwbG95X1lUcmF5LnB5JykucmVhZF90ZXh0KCkKbmV3X2Jsb2NrID0gJ0ZJTEVTID0gJyArIGpzb24uZHVtcHMoZW1iZWRkZWQsIGluZGVudD00KQpkZXBsb3kgPSByZS5zdWIocidGSUxFUyA9IFx7Lio/XH0nLCBuZXdfYmxvY2ssIGRlcGxveSwgZmxhZ3M9cmUuRE9UQUxMKQoKIyBBbHNvIHVwZGF0ZSBkZWZhdWx0IHZlcnNpb24KdmVyc2lvbiA9IGpzb24ubG9hZHMoUGF0aCgncGFja2FnZS5qc29uJykucmVhZF90ZXh0KCkpWyd2ZXJzaW9uJ10KZGVwbG95ID0gcmUuc3ViKHInLS12ZXJzaW9uIiwgZGVmYXVsdD0iW1xkLl0rIicsIGYnLS12ZXJzaW9uIiwgZGVmYXVsdD0ie3ZlcnNpb259IicsIGRlcGxveSkKClBhdGgoJ2RlcGxveV9ZVHJheS5weScpLndyaXRlX3RleHQoZGVwbG95KQpgYGAKCjQuIFZhbGlkYXRlOiBgcHl0aG9uMyAtYyAiaW1wb3J0IGFzdDsgYXN0LnBhcnNlKG9wZW4oJ2RlcGxveV9ZVHJheS5weScpLnJlYWQoKSk7IHByaW50KCdPSycpImAKNS4gQ29tbWl0IGFuZCBwdXNoIChkZXBsb3kgc2NyaXB0IGhhbmRsZXMgdGhpcyDigJQgc2VlIGJlbG93KQoKIyMgZGVwbG95X1lUcmF5LnB5IOKAlCB3aGF0IGl0IGRvZXMKClNpbmdsZSBQeXRob24gZmlsZSwgbm8gZGVwZW5kZW5jaWVzIGJleW9uZCBOb2RlLmpzIG9uIHRoZSBtYWNoaW5lLgoKMS4gRXh0cmFjdHMgYWxsIHNvdXJjZSBmaWxlcyBmcm9tIGVtYmVkZGVkIGJhc2U2NCBpbnRvIGBfeXRyYXlfYnVpbGQvYAoyLiBJbmplY3RzIGBlbGVjdHJvbi1idWlsZGVyYCBjb25maWcgaW50byBgcGFja2FnZS5qc29uYAozLiBSdW5zIGBucG0gaW5zdGFsbGAgaWYgYG5vZGVfbW9kdWxlc2Agbm90IHByZXNlbnQKNC4gQnVpbGRzIHBvcnRhYmxlIGAuZXhlYCB2aWEgYG5weCBlbGVjdHJvbi1idWlsZGVyIC0td2luIC0teDY0YAo1LiBNb3ZlcyBgWVRyYXktPHZlcnNpb24+LmV4ZWAgdG8gdGhlIHNjcmlwdCdzIGRpcmVjdG9yeQo2LiBEZWxldGVzIGBfeXRyYXlfYnVpbGQvYCBlbnRpcmVseQo3LiBPcHRpb25hbGx5IHB1c2hlcyBhbGwgcmVwbyBmaWxlcyB0byBHaXRIdWIgdmlhIHRoZSBBUEkKCiMjIEdpdEh1YiBwdXNoCgpUaGUgZGVwbG95IHNjcmlwdCBwcm9tcHRzIHRvIHB1c2ggdG8gR2l0SHViIGFmdGVyIGJ1aWxkaW5nLiBJdCB1c2VzIHRoZSBHaXRIdWIgQVBJIGRpcmVjdGx5IChubyBnaXQgYmluYXJ5IG5lZWRlZCkuIEl0IHdpbGw6Ci0gQ3JlYXRlIHRoZSByZXBvIGF0IGBnaXRodWIuY29tL2dyYW50ZXJvZ2Vycy9ZVHJheWAgaWYgaXQgZG9lc24ndCBleGlzdAotIFB1c2gvdXBkYXRlIGFsbCByZXBvIGZpbGVzIGluIG9uZSBjb21taXQKLSBUb2tlbiBpcyByZWFkIGZyb20gYEdJVEhVQl9UT0tFTmAgZW52IHZhciwgb3IgcHJvbXB0ZWQgaW50ZXJhY3RpdmVseQoKVG8gcHVzaCB3aXRob3V0IGJ1aWxkaW5nOgpgYGBiYXNoCnB5dGhvbiBkZXBsb3lfWVRyYXkucHkgLS1za2lwLWJ1aWxkCmBgYAoKIyMgU2hvcnRjdXQgcmVmZXJlbmNlCgp8IFNob3J0Y3V0IHwgRnVuY3Rpb24gfCBKUyB0YXJnZXQgfAp8LS0tfC0tLXwtLS18CnwgYEN0cmwrQWx0K1NwYWNlYCB8IFBsYXkgLyBQYXVzZSB8IGB2aWRlby5wbGF5KClgIC8gYHZpZGVvLnBhdXNlKClgIHwKfCBgQ3RybCtBbHQr4oaSYCB8IE5leHQgdHJhY2sgfCBgW2RhdGEtdGVzdGlkPSJuZXh0LWJ1dHRvbiJdYCBjbGljaywgZmFsbGJhY2sgU2hpZnQrTiB8CnwgYEN0cmwrQWx0K+KGkGAgfCBSZXN0YXJ0IC8gUHJldiB8IGB2aWRlby5jdXJyZW50VGltZSA9IDBgLCBvciBwcmV2IGJ1dHRvbiBpZiA8IDNzIHwKCiMjIEtub3duIGlzc3VlcyAvIGdvdGNoYXMKCi0gWW91VHViZSBNdXNpYyBwZXJpb2RpY2FsbHkgdXBkYXRlcyBpdHMgRE9NIOKAlCBpZiBuZXh0L3ByZXYgYnV0dG9uIHNlbGVjdG9ycyBicmVhaywgdXBkYXRlIHRoZSBgZGF0YS10ZXN0aWRgIHZhbHVlcyBpbiBgbWFpbi5qc2AKLSBUaGUgYHVzZXJhZ2VudGAgb3ZlcnJpZGUgaW4gYGluZGV4Lmh0bWxgIGlzIHJlcXVpcmVkIOKAlCB3aXRob3V0IGl0IFlvdVR1YmUgbWF5IHNlcnZlIGEgZGVncmFkZWQgZXhwZXJpZW5jZQotIE9uIGZpcnN0IGJ1aWxkLCBFbGVjdHJvbiAofjEwMCBNQikgZG93bmxvYWRzIGF1dG9tYXRpY2FsbHkgdmlhIGVsZWN0cm9uLWJ1aWxkZXIKLSBgc2hlbGw6IHRydWVgIGlzIHJlcXVpcmVkIGZvciBgbnBtYC9gbnB4YCBvbiBXaW5kb3dzICh0aGV5IGFyZSBgLmNtZGAgZmlsZXMpCg=="
}

# ── electron-builder config ──────────────────────────────────────────────────

def build_config():
    return {
        "appId": "com.ytray.app",
        "productName": "YTray",
        "directories": {"output": "dist"},
        "files": ["main.js", "index.html", "icon.png", "package.json"],
        "win": {
            "target": [{"target": "portable", "arch": ["x64"]}],
            "icon": "icon.png"
        }
    }

# ── Helpers ──────────────────────────────────────────────────────────────────

def log(msg, sym="->"):
    print(f"  {sym}  {msg}")

def run(cmd, cwd):
    log("Running: " + " ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, cwd=cwd, shell=(sys.platform == "win32"))
    if r.returncode != 0:
        print()
        print("  " + "="*60)
        print(f"  BUILD FAILED (exit code {r.returncode})")
        print("  " + "="*60)
        sys.exit(r.returncode)

# ── Build steps ──────────────────────────────────────────────────────────────

def extract_files(app_dir):
    app_dir.mkdir(parents=True, exist_ok=True)
    for name, b64 in FILES.items():
        dest = app_dir / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(base64.b64decode(b64))
        log(f"Extracted {name}", "OK")

def patch_package_json(app_dir, version):
    p = app_dir / "package.json"
    pkg = json.loads(p.read_text())
    pkg["version"] = version
    pkg["author"] = pkg.get("author", REPO_OWNER)
    pkg["build"] = build_config()
    pkg.setdefault("devDependencies", {})
    if "electron-builder" not in pkg["devDependencies"]:
        pkg["devDependencies"]["electron-builder"] = "^24.0.0"
    p.write_text(json.dumps(pkg, indent=2))
    log(f"package.json patched (v{version})", "OK")

def ensure_deps(app_dir):
    eb = app_dir / "node_modules" / ".bin" / "electron-builder.cmd"
    eb2 = app_dir / "node_modules" / ".bin" / "electron-builder"
    if not eb.exists() and not eb2.exists():
        log("Installing npm deps (first run downloads Electron ~100 MB)...")
        run(["npm", "install"], cwd=app_dir)
    else:
        log("npm deps already present", "OK")

def build_exe(app_dir):
    log("Building portable .exe...")
    run(["npx", "electron-builder", "--win", "--x64"], cwd=app_dir)

def collect_and_cleanup(app_dir, out_dir, version):
    dist = app_dir / "dist"
    exes = list(dist.glob("*.exe"))
    if not exes:
        print("  WARNING: no .exe found in dist/")
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"YTray-{version}.exe"
    shutil.move(str(exes[0]), str(dest))
    shutil.rmtree(app_dir)
    log(f"Build folder cleaned up", "OK")
    return dest

# ── GitHub push ──────────────────────────────────────────────────────────────

def gh_request(method, endpoint, token, data=None):
    url = f"https://api.github.com{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "deploy_YTray")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"GitHub API {e.code}: {body}")

def get_sha(path, token):
    try:
        r = gh_request("GET", f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}", token)
        return r.get("sha")
    except RuntimeError as e:
        if "404" in str(e): return None
        raise

def push_file(path, content_bytes, token, commit_msg):
    sha = get_sha(path, token)
    data = {
        "message": commit_msg,
        "content": base64.b64encode(content_bytes).decode()
    }
    if sha: data["sha"] = sha
    gh_request("PUT", f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}", token, data)
    log(f"Pushed {path}", "OK")

def ensure_repo(token):
    try:
        gh_request("GET", f"/repos/{REPO_OWNER}/{REPO_NAME}", token)
        log("Repo exists", "OK")
    except RuntimeError as e:
        if "404" not in str(e): raise
        gh_request("POST", "/user/repos", token, {
            "name": REPO_NAME, "private": False,
            "auto_init": False, "description": REPO_DESC
        })
        log(f"Created repo github.com/{REPO_OWNER}/{REPO_NAME}", "OK")

def push_to_github(version):
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print()
        print("  Enter your GitHub personal access token")
        print("  (needs repo scope — https://github.com/settings/tokens)")
        token = input("  Token: ").strip()
    if not token:
        print("  No token provided — skipping GitHub push.")
        return

    log("Connecting to GitHub...")
    ensure_repo(token)

    commit_msg = f"chore: release v{version}"
    repo_files = {
        "main.js":        "main.js",
        "index.html":     "index.html",
        "icon.png":       "icon.png",
        "package.json":   "package.json",
        "README.md":      "README.md",
        "LICENSE":        "LICENSE",
        ".gitignore":     ".gitignore",
        "AGENTS.md":      "AGENTS.md",
        "deploy_YTray.py":"deploy_YTray.py",
    }
    for repo_path, embed_key in repo_files.items():
        if embed_key == "deploy_YTray.py":
            content = Path(__file__).read_bytes()
        else:
            content = base64.b64decode(FILES[embed_key])
        push_file(repo_path, content, token, commit_msg)

    print()
    log(f"Published -> https://github.com/{REPO_OWNER}/{REPO_NAME}", "GH")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="YTray one-click builder")
    parser.add_argument("--version",    default="1.3.0", help="App version")
    parser.add_argument("--out",        default=None,  help="Output folder for .exe")
    parser.add_argument("--skip-build", action="store_true", help="Skip build, push to GitHub only")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    out_dir    = Path(args.out).resolve() if args.out else script_dir
    app_dir    = script_dir / "_ytray_build"

    print()
    print("  " + "="*60)
    print("  YTray Deploy  v" + args.version)
    print("  " + "="*60)
    print()

    dest = None
    if not args.skip_build:
        extract_files(app_dir)
        patch_package_json(app_dir, args.version)
        ensure_deps(app_dir)
        build_exe(app_dir)
        dest = collect_and_cleanup(app_dir, out_dir, args.version)
        print()
        print("  " + "="*60)
        if dest and dest.exists():
            mb = dest.stat().st_size / 1_048_576
            log(f"EXE ready:  {dest.name}  ({mb:.0f} MB)", "OK")
            log(f"Location:   {dest}", "OK")
        else:
            print("  Build may have failed — check output above")
        print("  " + "="*60)
    else:
        log("--skip-build set, skipping exe build")

    print()
    answer = input("  Push to GitHub? (Y/N): ").strip().upper()
    if answer == "Y":
        push_to_github(args.version)
    else:
        log("GitHub push skipped")

if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code != 0:
            print()
            print("  BUILD FAILED — see errors above")
    except Exception as e:
        print()
        print(f"  UNEXPECTED ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        print()
        input("  Press Enter to close...")