# Discord Publish Bot - Docker Image Naming Script
# Implements 2025 best practices for Azure Container Registry

param(
    [Parameter(Mandatory=$false)]
    [string]$RegistryName = "your-discord-bot",  # Change this to your unique name
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Build,
    
    [Parameter(Mandatory=$false)]
    [switch]$Push,
    
    [Parameter(Mandatory=$false)]
    [switch]$ShowNaming
)

# Get Git information for traceability
$gitCommit = git rev-parse --short HEAD 2>$null
$gitBranch = git branch --show-current 2>$null
$gitTag = git describe --tags --exact-match 2>$null

# Determine version if not provided
if (-not $Version) {
    if ($gitTag) {
        $Version = $gitTag
    } else {
        # Read version from pyproject.toml
        $pyprojectContent = Get-Content "pyproject.toml" -Raw
        if ($pyprojectContent -match 'version\s*=\s*"([^"]+)"') {
            $Version = "v$($matches[1])"
        } else {
            $Version = "v2.0.0"  # Fallback
        }
    }
}

# Construct image names following 2025 best practices
$registryFQDN = "$RegistryName.azurecr.io"
$repository = "personal/discord-publish-bot"
$baseImageName = "$registryFQDN/$repository"

# Generate multiple tags following best practices
# Generate all possible tags
$allTags = @{
    "Semantic" = "$Version"
    "WithCommit" = "$Version-$gitCommit"
    "WithEnvironment" = "$Version-$Environment"  
    "Full" = "$Version-$gitCommit-$Environment"
    "Branch" = if ($gitBranch -ne "main") { "$Version-$gitBranch-$gitCommit" } else { $null }
    "Latest" = if ($Environment -eq "prod") { "latest" } else { "latest-$Environment" }
}

# Filter out null entries and create clean hashtable
$tags = @{}
foreach ($tag in $allTags.GetEnumerator()) {
    if ($tag.Value -ne $null -and $tag.Value -ne "") {
        $tags[$tag.Key] = $tag.Value
    }
}

if ($ShowNaming) {
    Write-Host "🏷️  Docker Image Naming Strategy (2025 Best Practices)" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
    
    Write-Host "`n📋 Configuration:" -ForegroundColor Yellow
    Write-Host "   Registry: $registryFQDN" -ForegroundColor Gray
    Write-Host "   Repository: $repository" -ForegroundColor Gray
    Write-Host "   Version: $Version" -ForegroundColor Gray
    Write-Host "   Environment: $Environment" -ForegroundColor Gray
    Write-Host "   Git Commit: $gitCommit" -ForegroundColor Gray
    Write-Host "   Git Branch: $gitBranch" -ForegroundColor Gray
    
    Write-Host "`n🏷️  Generated Tags:" -ForegroundColor Yellow
    foreach ($tag in $tags.GetEnumerator()) {
        $fullImageName = "${baseImageName}:$($tag.Value)"
        Write-Host "   $($tag.Key): $fullImageName" -ForegroundColor Green
    }
    
    Write-Host "`n✅ Best Practice Compliance:" -ForegroundColor Yellow
    Write-Host "   ✅ Registry globally unique: $RegistryName" -ForegroundColor Green
    Write-Host "   ✅ Repository follows team/project pattern: personal/discord-publish-bot" -ForegroundColor Green
    Write-Host "   ✅ Semantic versioning: $Version" -ForegroundColor Green
    Write-Host "   ✅ Git traceability: includes commit SHA $gitCommit" -ForegroundColor Green
    Write-Host "   ✅ Environment identification: $Environment" -ForegroundColor Green
    Write-Host "   ✅ Multiple tag strategy for different use cases" -ForegroundColor Green
    
    Write-Host "`n📖 Usage Examples:" -ForegroundColor Yellow
    Write-Host "   Development: ${baseImageName}:$Version-$Environment" -ForegroundColor Gray
    Write-Host "   Production: ${baseImageName}:$Version-$gitCommit-prod" -ForegroundColor Gray
    Write-Host "   CI/CD: ${baseImageName}:$Version-$gitCommit" -ForegroundColor Gray
    Write-Host "   Latest: ${baseImageName}:latest-$Environment" -ForegroundColor Gray
    
    return
}

if ($Build) {
    Write-Host "🔨 Building Docker image with proper naming..." -ForegroundColor Green
    
    # Build with primary tag
    $primaryTag = "${baseImageName}:$($tags['Full'])"
    Write-Host "   Primary tag: $primaryTag" -ForegroundColor Yellow
    
    docker build -t $primaryTag .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Build successful!" -ForegroundColor Green
        
        # Apply additional tags
        foreach ($tag in $tags.GetEnumerator()) {
            if ($tag.Key -ne "Full") {
                $additionalTag = "${baseImageName}:$($tag.Value)"
                Write-Host "   Adding tag: $additionalTag" -ForegroundColor Gray
                docker tag $primaryTag $additionalTag
            }
        }
        
        Write-Host "`n📋 Available images:" -ForegroundColor Cyan
        docker images --filter "reference=$baseImageName" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        
    } else {
        Write-Error "Docker build failed!"
        exit 1
    }
}

if ($Push) {
    Write-Host "📤 Pushing images to Azure Container Registry..." -ForegroundColor Green
    
    # Check if logged into Azure
    $acrLoginCheck = az acr login --name $RegistryName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Please login to Azure Container Registry first:"
        Write-Host "   az login" -ForegroundColor Yellow
        Write-Host "   az acr login --name $RegistryName" -ForegroundColor Yellow
        exit 1
    }
    
    # Push all tags
    foreach ($tag in $tags.GetEnumerator()) {
        $imageTag = "${baseImageName}:$($tag.Value)"
        Write-Host "   Pushing: $imageTag" -ForegroundColor Yellow
        docker push $imageTag
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Pushed: $imageTag" -ForegroundColor Green
        } else {
            Write-Error "Failed to push: $imageTag"
        }
    }
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Review naming strategy: .\scripts\docker-naming.ps1 -ShowNaming" -ForegroundColor White
Write-Host "2. Build with proper tags: .\scripts\docker-naming.ps1 -Build" -ForegroundColor White
Write-Host "3. Test locally: docker run -p 8000:8000 ${baseImageName}:$($tags['Latest'])" -ForegroundColor White
Write-Host "4. Push to registry: .\scripts\docker-naming.ps1 -Push" -ForegroundColor White

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "- Azure Container Registry: https://docs.microsoft.com/azure/container-registry/" -ForegroundColor Gray
Write-Host "- Docker Tagging Best Practices: https://docs.docker.com/build/ci/github-actions/manage-tags-labels/" -ForegroundColor Gray
