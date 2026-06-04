import { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Typography } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined, ProjectOutlined, ApiOutlined } from '@ant-design/icons'
import { healthCheck } from '../api'

const { Title } = Typography

export default function Dashboard() {
  const [health, setHealth] = useState<string>('checking...')

  useEffect(() => {
    healthCheck().then(r => setHealth(r.data.status)).catch(() => setHealth('unreachable'))
  }, [])

  return (
    <div>
      <Title level={3}>系统总览</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="后端状态" value={health} prefix={<ApiOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活跃项目" value={0} prefix={<ProjectOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已完成任务" value={0} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="排队中" value={0} prefix={<ClockCircleOutlined />} />
          </Card>
        </Col>
      </Row>
      <Card title="快速入门">
        <ol>
          <li>在 <strong>LLM 配置</strong> 页面添加 API Key</li>
          <li>在 <strong>项目管理</strong> 中创建项目并导入代码</li>
          <li>提交后系统将自动分析、生成测试用例并在沙箱中运行</li>
          <li>查看 <strong>评分对比</strong> 了解各组成绩</li>
        </ol>
      </Card>
    </div>
  )
}