import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, Card, Table, Typography, Tag, Space, message } from 'antd'
import { BarChartOutlined } from '@ant-design/icons'
import { compareSubmissions } from '../api'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const { Title: ATitle } = Typography

export default function CompareScores() {
  const { projectId } = useParams()
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleCompare = async () => {
    setLoading(true)
    try {
      const res = await compareSubmissions([
        { submission_id: 's1', submitter_name: '张三', analysis: { style_score: 90 }, tests: { total: 10, passed: 9, failed: 1 }, coverage: 80 },
        { submission_id: 's2', submitter_name: '李四', analysis: { style_score: 75 }, tests: { total: 10, passed: 6, failed: 4 }, coverage: 55 },
        { submission_id: 's3', submitter_name: '王五', analysis: { style_score: 95 }, tests: { total: 10, passed: 10, failed: 0 }, coverage: 92 },
      ])
      setResults(res.data)
      message.success('评分计算完成')
    } catch { message.error('评分失败') }
    finally { setLoading(false) }
  }

  const columns = [
    { title: '排名', render: (_: any, __: any, i: number) => i + 1, width: 60 },
    { title: '提交者', dataIndex: 'submitter_name' },
    { title: '总分', dataIndex: 'overall_score', render: (v: number) => v?.toFixed(1) },
    {
      title: '等级', dataIndex: 'grade',
      render: (g: string) => {
        const colors: Record<string, string> = { A: 'green', B: 'blue', C: 'orange', D: 'red' }
        return <Tag color={colors[g] || 'red'}>{g}</Tag>
      },
    },
    { title: '功能', render: (_: any, r: any) => r.dimension_scores?.functionality?.toFixed(1) },
    { title: '规范', render: (_: any, r: any) => r.dimension_scores?.code_style?.toFixed(1) },
    { title: '质量', render: (_: any, r: any) => r.dimension_scores?.code_quality?.toFixed(1) },
    { title: '覆盖率', render: (_: any, r: any) => r.dimension_scores?.test_coverage?.toFixed(1) },
  ]

  const radarOption = results.length > 0 ? {
    tooltip: {},
    legend: { data: results.map((r: any) => r.submitter_name) },
    radar: {
      indicator: [
        { name: '功能正确性', max: 100 },
        { name: '代码规范', max: 100 },
        { name: '代码质量', max: 100 },
        { name: '测试覆盖率', max: 100 },
        { name: '性能效率', max: 100 },
        { name: '文档注释', max: 100 },
      ],
    },
    series: [{
      type: 'radar',
      data: results.map((r: any) => ({
        name: r.submitter_name,
        value: [
          r.dimension_scores?.functionality || 0,
          r.dimension_scores?.code_style || 0,
          r.dimension_scores?.code_quality || 0,
          r.dimension_scores?.test_coverage || 0,
          r.dimension_scores?.performance || 0,
          r.dimension_scores?.documentation || 0,
        ],
      })),
    }],
  } : {}

  const barOption = results.length > 0 ? {
    tooltip: {},
    xAxis: { type: 'category', data: results.map((r: any) => r.submitter_name) },
    yAxis: { type: 'value', max: 100 },
    series: [{ type: 'bar', data: results.map((r: any) => r.overall_score), itemStyle: { color: '#1677ff' } }],
  } : {}

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <ATitle level={3} style={{ margin: 0 }}>评分对比</ATitle>
        <Button type="primary" icon={<BarChartOutlined />} loading={loading} onClick={handleCompare}>加载示例数据</Button>
      </div>

      {results.length > 0 && (
        <>
          <Card title="📊 排名表" style={{ marginBottom: 16 }}>
            <Table dataSource={results} columns={columns} rowKey="submission_id" pagination={false} />
          </Card>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Card title="🕸 雷达图对比">
              <ReactEChartsCore echarts={echarts} option={radarOption} style={{ height: 400 }} />
            </Card>
            <Card title="📉 总分柱状图">
              <ReactEChartsCore echarts={echarts} option={barOption} style={{ height: 300 }} />
            </Card>
          </Space>
        </>
      )}
    </div>
  )
}