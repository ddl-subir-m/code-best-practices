```tsx
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Spin, Alert } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import styled from 'styled-components';
import orderBy from 'lodash/orderBy';

// --- Types ---

type ProjectStatus = 'active' | 'archived' | 'failed';

interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  lastUpdated: string;
}

interface ProjectsApiResponse {
  projects: Project[];
}

// --- Constants ---

const STATUS_COLORS: Record<ProjectStatus, string> = {
  active: '#52C41A',
  failed: '#FF4D4F',
  archived: '#8C8C8C',
};

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: 'Active',
  failed: 'Failed',
  archived: 'Archived',
};

// --- Styled Components ---

const DashboardContainer = styled.div`
  padding: 24px;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 32px;
  color: #3f4547;
  margin: 0;
`;

const SearchWrapper = styled.div`
  width: 320px;
`;

const CardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
`;

const ProjectCard = styled.div`
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
  background: #fff;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
    border-color: #3b3bd3;
  }
`;

const ProjectName = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #3f4547;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const ProjectMeta = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const StatusBadge = styled.span<{ $color: string }>`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: ${({ $color }) => $color};

  &::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: ${({ $color }) => $color};
  }
`;

const LastUpdated = styled.span`
  font-size: 13px;
  color: #7f8385;
`;

const SpinnerWrapper = styled.div`
  display: flex;
  justify-content: center;
  padding: 80px 0;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 64px 0;
  color: #7f8385;
  font-size: 14px;
`;

// --- Helpers ---

function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// --- Component ---

const ProjectHealthDashboard: React.FC = () => {
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function fetchProjects() {
      try {
        const response = await fetch('/v4/projects');
        if (!response.ok) {
          throw new Error(`Failed to fetch projects (${response.status})`);
        }
        const data: ProjectsApiResponse = await response.json();
        if (!cancelled) {
          setProjects(data.projects);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error
              ? err.message
              : 'An unexpected error occurred while loading projects.';
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchProjects();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredProjects = useMemo(() => {
    const sorted = orderBy(
      projects,
      [(p) => new Date(p.lastUpdated).getTime()],
      ['desc'],
    );
    if (!searchQuery.trim()) {
      return sorted;
    }
    const query = searchQuery.toLowerCase().trim();
    return sorted.filter((p) => p.name.toLowerCase().includes(query));
  }, [projects, searchQuery]);

  if (loading) {
    return (
      <DashboardContainer>
        <SpinnerWrapper>
          <Spin size="large" />
        </SpinnerWrapper>
      </DashboardContainer>
    );
  }

  if (error) {
    return (
      <DashboardContainer>
        <Alert
          type="error"
          showIcon
          message="Unable to load projects"
          description={`${error} Try refreshing the page. If the problem persists, contact your administrator.`}
        />
      </DashboardContainer>
    );
  }

  return (
    <DashboardContainer>
      <Header>
        <Title>Project health</Title>
        <SearchWrapper>
          <Input
            placeholder="Search projects by name"
            prefix={<SearchOutlined />}
            allowClear
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </SearchWrapper>
      </Header>

      {filteredProjects.length === 0 ? (
        <EmptyState>
          {searchQuery.trim()
            ? `No projects match "${searchQuery}". Try adjusting your search.`
            : 'No projects found. Create a project to get started.'}
        </EmptyState>
      ) : (
        <CardGrid>
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              role="link"
              aria-label={`View ${project.name} project overview`}
              onClick={() => navigate(`/projects/${project.id}/overview`)}
            >
              <ProjectName title={project.name}>
                {project.name}
              </ProjectName>
              <ProjectMeta>
                <StatusBadge $color={STATUS_COLORS[project.status]}>
                  {STATUS_LABELS[project.status]}
                </StatusBadge>
                <LastUpdated>
                  Updated {formatDate(project.lastUpdated)}
                </LastUpdated>
              </ProjectMeta>
            </ProjectCard>
          ))}
        </CardGrid>
      )}
    </DashboardContainer>
  );
};

export default ProjectHealthDashboard;
```
