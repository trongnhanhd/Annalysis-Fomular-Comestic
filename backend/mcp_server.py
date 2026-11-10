"""Read-only MCP surface for ChatGPT/Codex (MCP Python SDK v2).

The R&D App (protected REST API) is the only surface that creates/reviews records.
Never automatically convert user research drafts into verified scientific evidence.
"""
from __future__ import annotations
from mcp.server import MCPServer
from sqlalchemy import select
from engine import analyze
from evidence_catalog import find_studies, find_limits, find_preservation_systems
from workspace_db import SessionLocal, initialize_database, Product, ResearchRecord, AnalysisRun
from workspace_api import as_product, as_research, as_analysis

mcp = MCPServer('Cosmetic R&D — INCI & Evidence')

@mcp.tool()
def analyze_inci(inci: str, market: str = 'VN', product_type: str = 'leave_on') -> dict:
    """Tính khoảng % KHẢ THI từ nhãn INCI; không dự báo % thực, độ an toàn hay hiệu lực bảo quản.

    market: EU, US, KR, CN, VN hoặc ASEAN. Không tự áp giới hạn pháp lý khi chưa xác minh.
    """
    return analyze({'inci': inci, 'market': market.upper(), 'product_type': product_type})

@mcp.tool()
def analyze_confirmed_ingredient_percentage(inci: str, ingredient: str, exact_percent: float, evidence_source: str, market: str = 'VN') -> dict:
    """Phân tích nhãn với % w/w chính xác của INCI tinh khiết đã kiểm chứng.

    Chỉ dùng khi evidence_source mô tả bằng chứng về thành phần tinh khiết trong THÀNH PHẨM;
    không dùng cho % premix/complex, marketing claims mơ hồ hoặc nồng độ thử nghiệm.
    """
    if not evidence_source.strip():
        return {'error':'Cần dẫn nguồn để chốt tỷ lệ chính xác.'}
    return analyze({'inci': inci, 'market': market.upper(),
      'known_pct':{ingredient:{'value':exact_percent,'source':evidence_source}}})

@mcp.tool()
def search_curated_research(inci: str = '', category: str = '') -> dict:
    """Tra cứu bằng chứng khoa học V2.1 đã tuyển chọn; không phải toàn bộ PubMed."""
    return {'records':find_studies(inci=inci or None, category=category or None),
      'disclaimer':'Nồng độ nghiên cứu không phải nồng độ tối ưu; không dùng làm giới hạn pháp lý.'}

@mcp.tool()
def compare_regulatory_references(inci: str, market: str = '') -> dict:
    """Tra cứu các mục pháp lý V2.1 đã chọn; thiếu dữ liệu KHÔNG nghĩa là hợp pháp."""
    data=find_limits(inci=inci, market=market.upper() or None)
    return {'records':data,'coverage':'partial', 'warning':'Dữ liệu pháp lý không đầy đủ cho 6 thị trường, luôn xác nhận văn bản hiện hành.'}

@mcp.tool()
def search_preservation_systems(inci: str = '') -> dict:
    """Đối chiếu tổ hợp bảo quản trong nghiên cứu, không dự đoán challenge-test."""
    return {'records':find_preservation_systems(inci=inci or None),
      'warning':'Không suy ra đạt ISO 11930 hay điều kiện bảo quản của công thức khác.'}

@mcp.tool()
def list_research_products(name_contains: str = '', limit: int = 20) -> list[dict]:
    """Tìm sản phẩm đã lưu trong thư viện R&D (đọc dữ liệu riêng tư từ DB được cấp quyền)."""
    limit=max(1,min(limit,100))
    with SessionLocal() as db:
        query=select(Product).order_by(Product.created_at.desc()).limit(limit)
        if name_contains.strip(): query=query.where(Product.name.ilike(f'%{name_contains.strip()}%'))
        return [as_product(p) for p in db.scalars(query).all()]

@mcp.tool()
def get_saved_product(product_id: str) -> dict:
    """Đọc sản phẩm từ thư viện; không tiết lộ thông tin tài khoản hay token."""
    with SessionLocal() as db:
        p=db.get(Product,product_id)
        return as_product(p) if p else {'error':'Không tìm thấy sản phẩm'}

@mcp.tool()
def list_saved_analyses(product_id: str, limit: int = 10) -> list[dict]:
    """Đọc lịch sử phân tích đã lưu, gồm phiên bản bằng chứng của từng lần chạy."""
    with SessionLocal() as db:
        q=select(AnalysisRun).where(AnalysisRun.product_id==product_id).order_by(AnalysisRun.created_at.desc()).limit(max(1,min(limit,100)))
        return [as_analysis(a,full=True) for a in db.scalars(q).all()]

@mcp.tool()
def search_workspace_research(inci: str = '', limit: int = 30) -> dict:
    """Đọc tài liệu nghiên cứu người dùng nhập; bao gồm trạng thái nháp/duyệt.
    KHÔNG sử dụng nghiên cứu chưa duyệt như bằng chứng định lượng đã xác minh.
    """
    with SessionLocal() as db:
        q=select(ResearchRecord).order_by(ResearchRecord.created_at.desc()).limit(max(1,min(limit,100)))
        if inci.strip(): q=q.where(ResearchRecord.inci.ilike(f'%{inci.strip()}%'))
        return {'records':[as_research(r) for r in db.scalars(q).all()],
                'disclaimer':'Bản ghi do người dùng bổ sung không tự nhập vào catalog hay LP.'}

if __name__ == '__main__':
    initialize_database()
    mcp.run(transport='stdio')
