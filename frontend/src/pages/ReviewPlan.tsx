import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, Card, Input, Typography, message, Space, Tag, Descriptions, List } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { generatePlan, getPlan, reviewPlan } from '../api'

const { Title } = Typography
const { TextArea } = Input

export default function ReviewPlan() {
  const { projectId } = useParams()
  const [code, setCode] = useState('')
  const [plan, setPlan] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!code.trim()) { message.warning('请输入代码'); return }
    setLoading(true)
    try {
      const res = await generatePlan({ code, language: 'python', project_name: `项目-${projectId}` })
      setPlan(res.data)
      message.success('检测计划已生成，请审核')
    } catch (e: any) { message.error(e.response?.data?.detail || '生成失败') }
    finally { setLoading(false) }
  }

  const handleReview = async (approved: boolean) => {
    if (!plan) return
    setLoading(true)
    try {
      await reviewPlan(plan.plan_id, { approve: approved, reviewer_name: '管理员' })
      setPlan({ ...plan, status: approved ? 'approved' : 'rejected' })
      message.success(approved ? '计划已批准，可以开始测试' : '计划已驳回')
    } catch (e: any) { message.error(e.response?.data?.detail || '审核失败') }
    finally { setLoading(false) }
  }

  return (
    <div>
      <Title level={3}>检测计划审核 {projectId && <Tag color="blue">项目: {projectId}</Tag>}</Title>

      {!plan && (
        <Card>
          <TextArea rows={8} placeholder="输入代码以生成检测计划..." value={code} onChange={e => setCode(e.target.value)} />
          <Button type="primary" loading={loading} onClick={handleGenerate} style={{ marginTop: 12 }}>
            生成检测计划
          </Button>
        </Card>
      )}

      {plan && (
        <>
          <Card title="📋 检测计划" style={{ marginBottom: 16 }}>
            <Descriptions column={2}>
              <Descriptions.Item label="计划ID">{plan.plan_id}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={plan.status === 'approved' ? 'green' : plan.status === 'rejected' ? 'red' : 'orange'}>
                  {plan.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="测试框架">{plan.test_framework}</Descriptions.Item>
              <Descriptions.Item label="预计耗时">{plan.estimated_duration_minutes} 分钟</Descriptions.Item>
            </Descriptions>

            <Title level={5} style={{ marginTop: 16 }}>计划测试用例</Title>
            <List size="small" dataSource={plan.test_cases_plan || []} renderItem={(item: any) => (
              <List.Item>
                <Tag color={item.priority === 'critical' ? 'red' : 'blue'}>{item.priority}</Tag>
                {item.description}
              </List.Item>
            )} />

            <Title level={5} style={{ marginTop: 16 }}>评分维度</Title>
            <List size="small" dataSource={plan.scoring_dimensions || []} renderItem={(item: any) => (
              <List.Item>📊 {item.name} — 权重: {item.weight}% ({item.scoring_type})</List.Item>
            )} />

            {plan.risk_notes?.length > 0 && (
              <>
                <Title level={5} style={{ marginTop: 16, color: '#faad14' }}>⚠ 风险提示</Title>
                {plan.risk_notes.map((note: string, i: number) => (
                  <p key={i} style={{ color: '#faad14' }}>• {note}</p>
                ))}
              </>
            )}
          </Card>

          {plan.status === 'pending_review' && (
            <Card>
              <Space>
                <Button type="primary" icon={<CheckCircleOutlined />} loading={loading} onClick={() => handleReview(true)}>
                  批准并执行
                </Button>
                <Button danger icon={<CloseCircleOutlined />} loading={loading} onClick={() => handleReview(false)}>
                  驳回
                </Button>
              </Space>
            </Card>
          )}
        </>
      )}
    </div>
  )
}