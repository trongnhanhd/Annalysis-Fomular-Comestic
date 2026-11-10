"""Browser E2E with a transport bridge to local FastAPI.
Browser navigation to localhost is restricted in this environment, so Playwright
renders the *actual HTML/CSS/JS source* using set_content while fetch() is
bridged to the actual local HTTP server. All backend calls are real.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import re

HOST='http://127.0.0.1:8765'
root=Path(__file__).resolve().parents[1]
webapp=root/'backend'/'webapp'
shots=root/'screenshots'
shots.mkdir(exist_ok=True)
assert urlopen(HOST+'/app').status==200
html=(webapp/'index.html').read_text()
html=re.sub(r'<link[^>]*>', '', html)
html=re.sub(r'<script[^>]*src=[^>]*></script>','',html)
css=(webapp/'app.css').read_text()
js=(webapp/'app.js').read_text()

def transport(path,method='GET',headers=None,body=None):
    req=Request(HOST+path, method=method, headers=headers or {},data=(body.encode() if isinstance(body,str) else body))
    try:
        with urlopen(req,timeout=15) as res:return {'status':res.status,'body':res.read().decode('utf-8')}
    except HTTPError as err:return {'status':err.code,'body':err.read().decode('utf-8')}

def setup(page):
    page.set_content(html)
    page.add_style_tag(content=css)
    page.expose_function('__py_bridge',transport)
    page.evaluate('''(()=>{window.fetch=async (path, options={})=>{
      const reply=await window.__py_bridge(path,options.method||'GET',options.headers||{},options.body||null);
      return new Response(reply.body,{status:reply.status,headers:{'Content-Type':'application/json'}});
    };return true;})()''')
    page.add_script_tag(content=js)
    page.wait_for_timeout(700)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':990},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)))
    setup(page)
    assert page.get_by_text('Phòng nghiên cứu mỹ phẩm').is_visible()
    assert page.locator('#status').inner_text().find('đã kết nối')>=0
    page.screenshot(path=str(shots/'01_tong_quan_desktop.png'),full_page=True)
    page.locator('[data-tab="analysis"]').click()
    page.locator('#loadExample').click()
    assert page.locator('#ingredientCount').inner_text().startswith('6 thành phần')
    page.locator('#analyzeButton').click()
    page.get_by_text('Có nghiệm khả thi').wait_for(timeout=15000)
    assert page.locator('#analysisResult .table tbody tr').count()>=6
    assert page.locator('#analysisResult').get_by_text('Niacinamide').is_visible()
    page.locator('[data-evidence="2"]').click()
    assert page.locator('#detail-2').is_visible()
    assert page.locator('#detail-2').get_by_text('Cải thiện một số dấu hiệu',exact=False).count()>=1
    page.screenshot(path=str(shots/'02_phan_tich_inci_desktop.png'),full_page=True)
    page.locator('#saveAnalysis').click()
    page.get_by_text('Đã lưu hồ sơ',exact=False).wait_for(timeout=15000)
    page.locator('[data-tab="products"]').click()
    assert page.get_by_text('Serum Niacinamide — dữ liệu minh họa').count()>=1
    page.screenshot(path=str(shots/'03_thu_vien_san_pham.png'),full_page=True)
    page.locator('[data-tab="research"]').click()
    assert page.locator('#studiesList .study').count()>=1
    page.screenshot(path=str(shots/'04_thu_vien_nghien_cuu.png'),full_page=True)
    page.locator('[data-tab="regulatory"]').click()
    assert page.locator('.market').count()==6
    page.screenshot(path=str(shots/'05_phap_ly_thi_truong.png'),full_page=True)
    page.locator('[data-tab="formulas"]').click()
    page.locator('#formulaProduct').select_option(label='Serum Niacinamide — dữ liệu minh họa (EU)')
    assert page.locator('#formulaItems tr').count()==6
    vals=[72,15,5,4,1,3]
    for i,v in enumerate(vals): page.locator('#formulaItems .item-pct').nth(i).fill(str(v))
    assert page.get_by_text('Tổng: 100% · Hợp lệ').is_visible()
    page.locator('#saveFormula').click()
    page.get_by_text('Đã lưu một phiên bản').wait_for(timeout=15000)
    page.screenshot(path=str(shots/'06_cong_thuc_gia_thuyet.png'),full_page=True)
    assert not errors, errors
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    mobile_errors=[]
    mobile.on('pageerror',lambda e:mobile_errors.append(str(e)))
    setup(mobile)
    mobile.locator('#mobileMenu').click()
    mobile.locator('[data-tab="analysis"]').click()
    mobile.locator('#loadExample').click()
    mobile.locator('#analyzeButton').click()
    mobile.get_by_text('Có nghiệm khả thi').wait_for(timeout=15000)
    mobile.screenshot(path=str(shots/'07_mobile_phan_tich_inci.png'),full_page=True)
    overflow=mobile.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1')
    if overflow:
        print('MOBILE OVERFLOW', mobile.evaluate('''() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth, out:[...document.querySelectorAll('*')].map(x=>({tag:x.tagName,cls:x.className, id:x.id,left:x.getBoundingClientRect().left,right:x.getBoundingClientRect().right})).filter(x=>x.right>innerWidth+2).slice(0,20)})'''))
    assert not overflow, 'Mobile document overflows horizontally'
    assert not mobile_errors,mobile_errors
    browser.close()
print('PASS: dashboard, API analysis, evidence, product saving, research, 6 markets, formula 100%, mobile, browser errors = 0')
