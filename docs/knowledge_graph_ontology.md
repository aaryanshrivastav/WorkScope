# LMIP Knowledge Graph Ontology

## Overview

This document defines the ontology for the LMIP Knowledge Graph, a sector-agnostic representation of the labor market spanning roles, skills, companies, and sectors.

**Design Principle**: Technology is one sector among many. The graph structure supports all industries equally.

## Core Hierarchy

```
Sector
  ↓ BELONGS_TO
Role Family
  ↓ CONTAINS
Canonical Role
  ↓ REQUIRES
Canonical Skill
  ↓ CATEGORIZED_AS
Skill Category
```

## Node Types

### 1. Sector
Represents industry sectors and subsectors.

**Properties**:
* `sector_key` (string, unique): Sector identifier (e.g., `TECH`, `HOSP`, `HEAL`)
* `sector_name` (string): Display name (e.g., `Technology`, `Hospitality`)
* `parent_sector` (string, nullable): Parent sector key for hierarchy
* `sector_level` (int): Hierarchy level (1 = primary, 2 = secondary)
* `naics_code` (string): NAICS classification code
* `keywords` (array<string>): Keywords for sector matching
* `is_active` (boolean): Whether sector is actively tracked

**Source**: `metadata/sectors.csv` → `gold.dim_sector`

**Example**:
```json
{
  "sector_key": "TECH",
  "sector_name": "Technology",
  "parent_sector": null,
  "sector_level": 1,
  "naics_code": "51",
  "keywords": ["information technology", "software", "tech"],
  "is_active": true
}
```

### 2. Role Family
Grouping of related roles within a sector.

**Properties**:
* `family_key` (string, unique): Family identifier (e.g., `ENG`, `HOSP_OPS`, `CLIN_CARE`)
* `family_name` (string): Display name (e.g., `Engineering`, `Hospitality Operations`)
* `sector_key` (string): Parent sector
* `description` (string): Family description

**Source**: `metadata/role_families.csv`

**Example**:
```json
{
  "family_key": "ENG",
  "family_name": "Engineering",
  "sector_key": "TECH",
  "description": "Software engineering and technical development roles"
}
```

### 3. Canonical Role
Standardized job role definition.

**Properties**:
* `role_key` (string, unique): Role identifier (e.g., `ENG_SWE`, `HOSP_MANAGER`)
* `canonical_role` (string): Standard role name (e.g., `Software Engineer`, `Hotel Manager`)
* `family_key` (string): Parent role family
* `sector_key` (string): Parent sector
* `seniority` (string): Seniority level (`junior`, `mid`, `senior`, `executive`)
* `is_manager` (boolean): Whether role involves people management
* `is_executive` (boolean): Whether role is executive-level
* `aliases` (array<string>): Alternative names for matching
* `is_active` (boolean): Whether role is actively tracked

**Source**: `metadata/canonical_roles.csv` → `gold.dim_role`

**Example**:
```json
{
  "role_key": "ENG_SWE",
  "canonical_role": "Software Engineer",
  "family_key": "ENG",
  "sector_key": "TECH",
  "seniority": "mid",
  "is_manager": false,
  "is_executive": false,
  "aliases": ["software engineer", "swe", "software dev"],
  "is_active": true
}
```

### 4. Canonical Skill
Standardized skill definition.

**Properties**:
* `skill_key` (string, unique): Skill identifier (e.g., `TECH_PYTHON`, `HOSP_REV_MGT`)
* `canonical_skill` (string): Standard skill name (e.g., `Python`, `Revenue Management`)
* `skill_category` (string): Category (`Technical`, `Operations`, `Clinical`, `Finance`, `Soft Skill`)
* `sector_key` (string, nullable): Primary sector (null for cross-sector soft skills)
* `is_technical` (boolean): Whether skill is technical in nature
* `demand_score` (float): Market demand metric (0.0-1.0)
* `aliases` (array<string>): Alternative names for matching
* `is_active` (boolean): Whether skill is actively tracked

**Source**: `metadata/canonical_skills.csv` → `gold.dim_skill`

**Example**:
```json
{
  "skill_key": "TECH_PYTHON",
  "canonical_skill": "Python",
  "skill_category": "Technical",
  "sector_key": "TECH",
  "is_technical": true,
  "demand_score": 0.95,
  "aliases": ["python", "py"],
  "is_active": true
}
```

### 5. Company
Employer entity.

**Properties**:
* `company_key` (string, unique): Company identifier
* `canonical_company_name` (string): Standardized company name
* `primary_sector_key` (string): Primary sector of operation
* `company_size` (string): Size category (`startup`, `small`, `medium`, `large`, `enterprise`)
* `headquarters_location` (string): HQ location
* `is_active` (boolean): Whether company is actively hiring

**Source**: `gold.dim_company`

**Example**:
```json
{
  "company_key": "COMP_001",
  "canonical_company_name": "Databricks",
  "primary_sector_key": "TECH",
  "company_size": "large",
  "headquarters_location": "San Francisco, CA",
  "is_active": true
}
```

### 6. Job Posting
Individual job posting instance.

**Properties**:
* `job_id` (string, unique): Job posting identifier
* `role_key` (string): Canonical role
* `company_key` (string): Employer
* `location` (string): Job location
* `salary_min` (float, nullable): Minimum salary
* `salary_max` (float, nullable): Maximum salary
* `posted_date` (timestamp): Posting date
* `is_remote` (boolean): Remote work option
* `is_active` (boolean): Whether posting is still open

**Source**: `gold.fact_job_postings`

**Example**:
```json
{
  "job_id": "JOB_12345",
  "role_key": "ENG_SWE",
  "company_key": "COMP_001",
  "location": "San Francisco, CA",
  "salary_min": 120000.0,
  "salary_max": 180000.0,
  "posted_date": "2025-06-01T00:00:00Z",
  "is_remote": true,
  "is_active": true
}
```

## Edge Types (Relationships)

### 1. BELONGS_TO
**From**: Role Family → Sector  
**From**: Canonical Role → Role Family  
**From**: Canonical Role → Sector  
**From**: Canonical Skill → Sector

**Properties**:
* `relationship_type` (string): Type of belonging (`primary`, `secondary`)
* `created_at` (timestamp): When relationship was established

**Example**:
```
(RoleFamily:ENG)-[BELONGS_TO]->(Sector:TECH)
(CanonicalRole:ENG_SWE)-[BELONGS_TO]->(RoleFamily:ENG)
(CanonicalSkill:TECH_PYTHON)-[BELONGS_TO]->(Sector:TECH)
```

### 2. CONTAINS
**From**: Sector → Role Family  
**From**: Role Family → Canonical Role

**Properties**:
* `count` (int): Number of entities contained
* `updated_at` (timestamp): Last update

**Example**:
```
(Sector:TECH)-[CONTAINS {count: 3}]->(RoleFamily:ENG)
(RoleFamily:ENG)-[CONTAINS {count: 15}]->(CanonicalRole:ENG_SWE)
```

### 3. REQUIRES
**From**: Canonical Role → Canonical Skill

**Properties**:
* `proficiency_level` (string): Required proficiency (`basic`, `intermediate`, `advanced`, `expert`)
* `importance_score` (float): How critical skill is to role (0.0-1.0)
* `frequency` (int): How often this skill appears in job postings for this role

**Example**:
```
(CanonicalRole:ENG_SWE)-[REQUIRES {proficiency_level: "advanced", importance_score: 0.95, frequency: 850}]->(CanonicalSkill:TECH_PYTHON)
```

### 4. CATEGORIZED_AS
**From**: Canonical Skill → Skill Category

**Properties**:
* `primary` (boolean): Whether this is the primary category

**Example**:
```
(CanonicalSkill:TECH_PYTHON)-[CATEGORIZED_AS {primary: true}]->(SkillCategory:Technical)
```

### 5. HIRES_FOR
**From**: Company → Canonical Role

**Properties**:
* `active_postings` (int): Number of current open positions
* `total_postings` (int): Total historical postings
* `avg_salary` (float): Average salary offered
* `first_posted` (timestamp): First time company posted for this role
* `last_posted` (timestamp): Most recent posting

**Example**:
```
(Company:COMP_001)-[HIRES_FOR {active_postings: 5, total_postings: 42, avg_salary: 150000.0}]->(CanonicalRole:ENG_SWE)
```

### 6. OPERATES_IN
**From**: Company → Sector

**Properties**:
* `is_primary` (boolean): Whether this is the company's primary sector
* `percentage` (float): Estimated percentage of business in this sector

**Example**:
```
(Company:COMP_001)-[OPERATES_IN {is_primary: true, percentage: 1.0}]->(Sector:TECH)
```

### 7. POSTED_FOR
**From**: Job Posting → Canonical Role  
**From**: Job Posting → Company

**Properties**:
* `posted_date` (timestamp): When posting was created
* `expires_date` (timestamp, nullable): When posting expires

**Example**:
```
(JobPosting:JOB_12345)-[POSTED_FOR]->(CanonicalRole:ENG_SWE)
(JobPosting:JOB_12345)-[POSTED_BY]->(Company:COMP_001)
```

### 8. REQUIRES_SKILL
**From**: Job Posting → Canonical Skill

**Properties**:
* `mentioned_count` (int): How many times skill appears in posting
* `is_required` (boolean): Whether marked as required vs. preferred
* `extracted_proficiency` (string, nullable): Proficiency level mentioned in posting

**Example**:
```
(JobPosting:JOB_12345)-[REQUIRES_SKILL {mentioned_count: 3, is_required: true}]->(CanonicalSkill:TECH_PYTHON)
```

### 9. RELATED_TO
**From**: Canonical Skill → Canonical Skill  
**From**: Canonical Role → Canonical Role

**Properties**:
* `similarity_score` (float): How similar entities are (0.0-1.0)
* `relationship_type` (string): Type of relationship (`prerequisite`, `complement`, `alternative`)

**Example**:
```
(CanonicalSkill:TECH_PYTHON)-[RELATED_TO {similarity_score: 0.85, relationship_type: "complement"}]->(CanonicalSkill:TECH_SQL)
(CanonicalRole:ENG_SWE)-[RELATED_TO {similarity_score: 0.75, relationship_type: "alternative"}]->(CanonicalRole:DATA_DS)
```

## Graph Traversal Patterns

### Pattern 1: Role-to-Skills
Find all skills required for a role:
```cypher
MATCH (r:CanonicalRole {role_key: 'ENG_SWE'})-[req:REQUIRES]->(s:CanonicalSkill)
RETURN s.canonical_skill, req.proficiency_level, req.importance_score
ORDER BY req.importance_score DESC
```

### Pattern 2: Sector Skills Landscape
Find all skills in a sector:
```cypher
MATCH (sec:Sector {sector_key: 'TECH'})<-[:BELONGS_TO]-(r:CanonicalRole)-[req:REQUIRES]->(s:CanonicalSkill)
RETURN s.canonical_skill, COUNT(r) as role_count, AVG(req.importance_score) as avg_importance
ORDER BY role_count DESC
```

### Pattern 3: Company Hiring Landscape
Find what roles and skills a company is hiring for:
```cypher
MATCH (c:Company {company_key: 'COMP_001'})-[:HIRES_FOR]->(r:CanonicalRole)-[:REQUIRES]->(s:CanonicalSkill)
RETURN r.canonical_role, COLLECT(DISTINCT s.canonical_skill) as required_skills
```

### Pattern 4: Cross-Sector Role Similarities
Find similar roles across sectors:
```cypher
MATCH (r1:CanonicalRole {sector_key: 'TECH'})-[:REQUIRES]->(s:CanonicalSkill)<-[:REQUIRES]-(r2:CanonicalRole)
WHERE r1 <> r2 AND r2.sector_key <> 'TECH'
RETURN r1.canonical_role, r2.canonical_role, r2.sector_key, COUNT(s) as shared_skills
ORDER BY shared_skills DESC
```

### Pattern 5: Skill Demand by Sector
Find which sectors demand a particular skill:
```cypher
MATCH (s:CanonicalSkill {skill_key: 'TECH_PYTHON'})<-[req:REQUIRES]-(r:CanonicalRole)-[:BELONGS_TO]->(sec:Sector)
RETURN sec.sector_name, COUNT(r) as role_count, AVG(req.importance_score) as avg_importance
ORDER BY role_count DESC
```

### Pattern 6: Career Pathways
Find progression paths between roles:
```cypher
MATCH path = (r1:CanonicalRole {role_key: 'ENG_SWE_JR'})-[:RELATED_TO*1..2 {relationship_type: 'progression'}]->(r2:CanonicalRole)
WHERE r2.seniority IN ['senior', 'executive']
RETURN path
```

## Implementation Strategy

### Phase 1: Core Taxonomy (Current)
* ✅ Define node types and properties
* ✅ Build metadata foundation (sectors, roles, skills)
* ✅ Refactor intermediate layer to use metadata
* ✅ Update gold dimensions

### Phase 2: Graph Construction
* Load nodes from gold dimensions
* Build BELONGS_TO and CONTAINS edges from taxonomy
* Build REQUIRES edges from job posting analysis
* Build HIRES_FOR and OPERATES_IN edges from company data

### Phase 3: Enrichment
* Build RELATED_TO edges using similarity analysis
* Add REQUIRES_SKILL edges from job postings
* Compute demand_score and importance_score from evidence
* Build career pathway edges

### Phase 4: Analytics & Queries
* Implement graph traversal queries
* Build recommendation engines (role suggestions, skill gaps, career paths)
* Create graph-based dashboards

## Technology Stack

**Graph Database**: Neo4j or TigerGraph  
**ETL**: PySpark (from Unity Catalog to Graph DB)  
**Query Language**: Cypher (Neo4j) or GSQL (TigerGraph)  
**Visualization**: Neo4j Bloom or custom D3.js

## Data Lineage

```
metadata/*.csv
  ↓ (loaded by intermediate notebooks)
intermediate.*
  ↓ (transformed by gold notebooks)
gold.dim_*
  ↓ (exported for graph construction)
Graph Database (Neo4j/TigerGraph)
  ↓ (queried for insights)
Dashboards & Applications
```

## Benefits of This Ontology

1. **Sector-Agnostic**: Technology, Hospitality, Healthcare all supported equally
2. **Scalable**: Add sectors/roles/skills via metadata, not code changes
3. **Evidence-Based**: Relationships derived from actual job posting data
4. **Traversable**: Rich query patterns for insights and recommendations
5. **Future-Proof**: When new sectors arrive, graph structure is ready
6. **Governed**: Single source of truth in metadata files

## See Also

* [Metadata README](../metadata/README_METADATA.md) - Source taxonomy definitions
* [metadata_loader notebook](../notebooks/intermediate/metadata_loader.ipynb) - How metadata is loaded
* [Gold dimension notebooks](../notebooks/gold/) - Graph node sources