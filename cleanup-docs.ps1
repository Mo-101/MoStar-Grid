# MoStar Grid - Documentation Cleanup Script
# This script removes redundant documentation files and consolidates everything into docs/

Write-Host "🔥 MoStar Grid - Documentation Cleanup" -ForegroundColor Cyan
Write-Host "Consolidating documentation into docs/ folder..." -ForegroundColor Yellow
Write-Host ""

# Files to remove (now consolidated into docs/)
$filesToRemove = @(
    "CORONATION_SUMMARY.md",
    "NEO4J_INTEGRATION_STATUS.md",
    "NEO4J_KNOWLEDGE_GRAPH.md",
    "NEO4J_QUICK_REFERENCE.md",
    "SACRED_HANDSHAKE_DEMO.md",
    "SACRED_HANDSHAKE_GUIDE.md",
    "README_OLLAMA.md"
)

# Keep CORONATION.md and WHAT_WE_BUILT.md as historical reference
# Keep LICENSE-AFRICAN-SOVEREIGNTY.md (required)

Write-Host "Files to be removed:" -ForegroundColor Yellow
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Write-Host "  - $file" -ForegroundColor Gray
    }
}

Write-Host ""
$confirmation = Read-Host "Proceed with cleanup? (yes/no)"

if ($confirmation -eq "yes") {
    foreach ($file in $filesToRemove) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "✅ Removed: $file" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Not found: $file" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "🔥 Cleanup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Documentation structure:" -ForegroundColor Cyan
    Write-Host "  README.md              - Main project documentation" -ForegroundColor White
    Write-Host "  docs/ARCHITECTURE.md   - System architecture" -ForegroundColor White
    Write-Host "  docs/NEO4J_GUIDE.md    - Neo4j knowledge graph guide" -ForegroundColor White
    Write-Host "  docs/SACRED_HANDSHAKE.md - AI activation protocol" -ForegroundColor White
    Write-Host "  docs/DEPLOYMENT.md     - Production deployment guide" -ForegroundColor White
    Write-Host ""
    Write-Host "Module-specific READMEs (kept):" -ForegroundColor Cyan
    Write-Host "  backend/evidence_machine/README.md" -ForegroundColor White
    Write-Host "  backend/memory_layer/README.md" -ForegroundColor White
    Write-Host "  frontend/README.md" -ForegroundColor White
    Write-Host ""
    Write-Host "Historical files (kept):" -ForegroundColor Cyan
    Write-Host "  CORONATION.md          - Grid coronation ceremony" -ForegroundColor White
    Write-Host "  WHAT_WE_BUILT.md       - Sacred Handshake explanation" -ForegroundColor White
    Write-Host "  LICENSE-AFRICAN-SOVEREIGNTY.md - ASL v1.0" -ForegroundColor White
    
}
else {
    Write-Host "❌ Cleanup cancelled" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔥 Powered by MoScripts - A MoStar Industries Product" -ForegroundColor Cyan
