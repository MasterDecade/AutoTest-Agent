import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Button, Card, Input, Typography, message, Space, Tag, Descriptions, List, Divider, Alert, Spin } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { getPlan, reviewPlan, generateAndRun } from '../api'

const { Title } = Typography
const { TextArea } = Input

export default function ReviewPlan() {
  const { projectId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [plan, setPlan] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [reviewNotes, setReviewNotes] = useState('')

  // Load plan from plan_id query param or fetch the first approved plan
  useEffect(() => {
    const planId = searchParams.get('plan_id')
    if (planId) {
      setLoading(true)
      getPlan(planId)
        .then(res => setPlan(res.data))
        .catch(() => message.error('加载检测计划失败'))
        .finally(() => setLoading(false))
    }
  }, [searchParams])

  const handleReview = async (approved: boolean) => {
    if (!plan) return
    setLoading(true)
    try {
      await reviewPlan(plan.plan_id, {
        approve: approved,
        reviewer_name: '管理员',
        reviewer_notes: reviewNotes,
      })
      setPlan({ ...plan, status: approved ? 'approved' : 'rejected', reviewer_notes: reviewNotes })
      message.success(approved ? '计划已批准，可以执行测试' : '计划已驳回')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '审核失败')
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!plan) return
    setExecuting(true)
    try {
      // Use the plan's environment config to construct a test execution
      const code = plan.test_cases_plan
        ?.map((tc: any) => `// ${tc.id}: ${tc.description}`)
        .join('\n') || '# Sample code from plan'

      const res = await generateAndRun({
        code,
        language: plan.languages?.[0] || 'python',
        num_cases: Math.min(plan.test_cases_plan?.length || 5, 20),
      })
      setTestResult(res.data)
      setPlan({ ...plan, status: 'executed' })
      message.success('测试执行完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '测试执行失败')
    } finally {
      setExecuting(false)
    }
  }

  if (loading && !plan) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>加载检测计划中...</p>
      </div>
    )
  }

  if (!plan) {
    return (
      <div>
        <Title level={3}>检测计划审核</Title>
        <Card>
          <Alert
            type="info"
            message="未找到检测计划"
            description="请先在「项目内容」页面中上传文档或输入需求，并生成检测计划。"
            showIcon
          />
          <Button type="primary" style={{ marginTop: 16 }}
            onClick={() => navigate(`/projects/${projectId}/content`)}>
            前往项目内容页面
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Title level={3}>
        检测计划审核
        {projectId && <Tag color="blue" style={{ marginLeft: 8 }}>项目: {projectId}</Tag>}
      </Title>

      <Card title="📋 检测计划" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="计划ID">{plan.plan_id}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={
              plan.status === 'approved' ? 'green' :
              plan.status === 'rejected' ? 'red' :
              plan.status === 'executed' ? 'purple' : 'orange'
            }>
              {plan.status === 'pending_review' ? '待审核' :
               plan.status === 'approved' ? '已批准' :
               plan.status === 'rejected' ? '已驳回' :
               plan.status === 'executed' ? '已执行' : plan.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="语言">{plan.languages?.join(', ')}</Descriptions.Item>
          <Descriptions.Item label="测试框架">{plan.test_framework}</Descriptions.Item>
          <Descriptions.Item label="预计耗时">{plan.estimated_duration_minutes} 分钟</Descriptions.Item>
          <Descriptions.Item label="文件数">{plan.files_to_analyze}</Descriptions.Item>
        </Descriptions>

        {plan.reviewer_notes && (
          <Alert
            type={plan.status === 'rejected' ? 'warning' : 'info'}
            message={`审核意见: ${plan.reviewer_notes}`}
            style={{ marginTop: 12 }}
            showIcon
          />
        )}

        <Divider orientation="left">计划测试用例</Divider>
        <List size="small" dataSource={plan.test_cases_plan || []}
          locale={{ emptyText: '无计划测试用例' }}
          renderItem={(item: any) => (
            <List.Item>
              <Space>
                <Tag color={
                  item.priority === 'critical' ? 'red' :
                  item.priority === 'high' ? 'orange' : 'blue'
                }>{item.priority || 'medium'}</Tag>
                <Tag>{item.category || '未分类'}</Tag>
                {item.description}
                {item.estimated_count > 1 && <Tag>×{item.estimated_count}</Tag>}
              </Space>
            </List.Item>
          )} />

        <Divider orientation="left">评分维度</Divider>
        <List size="small" dataSource={plan.scoring_dimensions || []}
          locale={{ emptyText: '无评分维度' }}
          renderItem={(item: any) => (
            <List.Item>📊 {item.name} — 权重: {item.weight}% ({item.scoring_type})</List.Item>
          )} />

        {plan.code_style_checks?.length > 0 && (
          <>
            <Divider orientation="left">代码风格检查</Divider>
            <List size="small" dataSource={plan.code_style_checks}
              renderItem={(item: string) => <List.Item>🔍 {item}</List.Item>} />
          </>
        )}

        {plan.risk_notes?.length > 0 && (
          <Alert
            type="warning"
            message="⚠ 风险提示"
            description={plan.risk_notes.map((note: string, i: number) => (
              <p key={i} style={{ margin: 0 }}>• {note}</p>
            ))}
            style={{ marginTop: 12 }}
            showIcon
          />
        )}
      </Card>

      {/* Action buttons based on plan status */}
      {plan.status === 'pending_review' && (
        <Card title="审核操作">
          <TextArea
            rows={2}
            placeholder="审核意见（可选）..."
            value={reviewNotes}
            onChange={e => setReviewNotes(e.target.value)}
            style={{ marginBottom: 12 }}
          />
          <Space>
            <Button
              type="primary"
              size="large"
              icon={<CheckCircleOutlined />}
              loading={loading}
              onClick={() => handleReview(true)}
            >
              批准计划
            </Button>
            <Button
              danger
              size="large"
              icon={<CloseCircleOutlined />}
              loading={loading}
              onClick={() => handleReview(false)}
            >
              驳回计划
            </Button>
          </Space>
        </Card>
      )}

      {plan.status === 'approved' && (
        <Card title="执行操作">
          <Alert
            type="success"
            message="计划已批准，可以执行测试"
            description="点击下方按钮将在沙箱环境中生成测试用例并执行。"
            style={{ marginBottom: 16 }}
            showIcon
          />
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            loading={executing}
            onClick={handleExecute}
          >
            执行计划
          </Button>
        </Card>
      )}

      {plan.status === 'executed' && (
        <Card title="执行完成">
          <Alert
            type="success"
            message="计划已执行完成"
            description="可以前往「评分对比」页面查看测试评分结果。"
            style={{ marginBottom: 16 }}
            showIcon
          />
          <Button onClick={() => navigate(`/projects/${projectId}/compare`)}>
            查看评分对比
          </Button>
        </Card>
      )}

      {/* Test Results */}
      {testResult && (
        <Card title="🧪 测试执行结果" style={{ marginTop: 16 }}>
          <Descriptions column={4} size="small">
            <Descriptions.Item label="总用例">{testResult.total}</Descriptions.Item>
            <Descriptions.Item label="通过">
              <span style={{ color: '#52c41a' }}>{testResult.passed}</span>
            </Descriptions.Item>
            <Descriptions.Item label="失败">
              <span style={{ color: '#ff4d4f' }}>{testResult.failed}</span>
            </Descriptions.Item>
            <Descriptions.Item label="错误">{testResult.errors}</Descriptions.Item>
            <Descriptions.Item label="通过率">{testResult.pass_rate}%</Descriptions.Item>
            <Descriptions.Item label="覆盖率">{testResult.coverage}%</Descriptions.Item>
            <Descriptions.Item label="耗时">{testResult.duration_ms}ms</Descriptions.Item>
            <Descriptions.Item label="超时">{testResult.timed_out ? '是' : '否'}</Descriptions.Item>
          </Descriptions>
          {testResult.stdout && (
            <pre style={{
              background: '#f5f5f5', padding: 12, borderRadius: 4,
              maxHeight: 300, overflow: 'auto', marginTop: 8, fontSize: 12,
            }}>
              {testResult.stdout}
            </pre>
          )}
        </Card>
      )}
    </div>
  )
}
