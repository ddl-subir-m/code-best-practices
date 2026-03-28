Here's the code:

```tsx
import React, { useEffect, useMemo, useState } from 'react';
import { Card, Input, Spin, Alert, Tag, Typography, Row, Col } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import orderBy from 'lodash/orderBy';

const { Text, Title } = Typography;

interface Project {
  id: string;
  name: string;
  status: 'active' | 'archived' | 'failed';
  updatedAt: string;
}

const STATUS_CONFIG: Record<Project['status'], { color: string; label: string }> = {
  active: { color: 'green', label: 'Active' },
  failed: { color: 'red', label: 'Failed' },
  archived: { color: 'default', label: 'Archived' },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays < 1) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays <= 7) return `${diffDays} days ago`;

  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

const ProjectHealthDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    async function fetchProjects() {
      try {
        const response = await fetch('/v4/projects', { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Failed to fetch projects (${response.status})`);
        }
        const data: Project[] = await response.json();
        setProjects(data);
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setError(err instanceof Error ? err.message : 'An unexpected error occurred while loading projects.');
      } finally {
        setLoading(false);
      }
    }

    fetchProjects();
    return () => controller.abort();
  }, []);

  const filteredProjects = useMemo(() => {
    const query = searchQuery.toLowerCase().trim();
    const filtered = query
      ? projects.filter((p) => p.name.toLowerCase().includes(query))
      : projects;
    return orderBy(filtered, ['updatedAt'], ['desc']);
  }, [projects, searchQuery]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 320 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        message="Unable to load projects"
        description={error}
        style={{ margin: 24 }}
      />
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ color: '#3F4547', marginBottom: 16 }}>
        Project health
      </Title>

      <Input
        placeholder="Search projects by name"
        prefix={<SearchOutlined />}
        allowClear
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        style={{ maxWidth: 400, marginBottom: 24 }}
      />

      {filteredProjects.length === 0 ? (
        <Alert
          type="info"
          showIcon
          message="No projects found"
          description={
            searchQuery
              ? 'Try adjusting your search terms.'
              : 'No projects exist yet. Create a project to get started.'
          }
        />
      ) : (
        <Row gutter={[16, 16]}>
          {filteredProjects.map((project) => {
            const { color, label } = STATUS_CONFIG[project.status];
            return (
              <Col key={project.id} xs={24} sm={12} lg={8} xl={6}>
                <Card
                  hoverable
                  onClick={() => navigate(`/projects/${project.id}/overview`)}
                  style={{ borderColor: '#DBE4E8', height: '100%' }}
                >
                  <Text strong style={{ color: '#3F4547', fontSize: 16, display: 'block', marginBottom: 8 }}>
                    {project.name}
                  </Text>
                  <Tag color={color}>{label}</Tag>
                  <Text
                    type="secondary"
                    style={{ display: 'block', marginTop: 12, fontSize: 12, color: '#7F8385' }}
                  >
                    Updated {formatDate(project.updatedAt)}
                  </Text>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );
};

export default ProjectHealthDashboard;
```
