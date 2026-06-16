<script setup lang="ts">
import { onMounted, ref } from 'vue'; import { gradeApi, type GradeSummary, type GradedSubmission } from '../api/grades'; import ScoreDisplay from '../components/common/ScoreDisplay.vue'; import StatusTag from '../components/common/StatusTag.vue'; import { ElMessage, ElMessageBox } from 'element-plus';
const summary = ref<GradeSummary>({ average:0, highest:0, lowest:0, pass_rate:0, rows:[] }); const submissions = ref<GradedSubmission[]>([]); const loading = ref(false); const gradeFilter = ref<string>('');
async function fetchAll() { loading.value = true; try { const [s, list] = await Promise.all([ gradeApi.summary(), gradeApi.listGraded(gradeFilter.value ? { grade_status: gradeFilter.value as any } : undefined) ]); summary.value = s; submissions.value = list; } finally { loading.value = false; } }
onMounted(fetchAll);
async function handleGrade(row: GradedSubmission) { const { value } = await ElMessageBox.prompt('请输入分数', '评分', { inputValue: row.score?.toString() || '', inputPattern: /^\d+(\.\d+)?$/, inputErrorMessage: '请输入有效分数' }); await gradeApi.grade(row.id, { score: parseFloat(value) }); ElMessage.success('评分成功'); fetchAll(); }
async function handlePublish() { const draftIds = submissions.value.filter(s => s.grade_status === 'DRAFT').map(s => s.id); if (!draftIds.length) { ElMessage.warning('没有待发布的成绩'); return; } await ElMessageBox.confirm(`确认发布 ${draftIds.length} 条成绩？发布后学生将可见。`, '发布成绩'); const res = await gradeApi.publish({ submission_ids: draftIds }); ElMessage.success(`已发布 ${res.published_count} 条成绩`); fetchAll(); }
</script>
<template>
<section class="page">
  <header><h2>成绩管理</h2><div class="actions"><el-select v-model="gradeFilter" placeholder="筛选状态" clearable style="width:120px;margin-right:12px" @change="fetchAll"><el-option label="待发布" value="DRAFT"/><el-option label="已发布" value="PUBLISHED"/></el-select><el-button v-permission="['ADMIN','TEACHER']" type="success" @click="handlePublish">发布成绩</el-button><el-button v-permission="['ADMIN','TEACHER']">导出 Excel</el-button></div></header>
  <div class="metrics"><el-statistic title="平均分" :value="summary.average"/><el-statistic title="最高分" :value="summary.highest"/><el-statistic title="最低分" :value="summary.lowest"/><el-statistic title="及格率" :value="summary.pass_rate" suffix="%"/></div>
  <el-table :data="submissions" v-loading="loading" style="margin-top:20px">
    <el-table-column prop="student_name" label="学生"/>
    <el-table-column label="分数"><template #default="{row}"><ScoreDisplay :score="row.score" :total-score="100"/></template></el-table-column>
    <el-table-column prop="comment" label="评语"/>
    <el-table-column label="状态" width="100"><template #default="{row}"><el-tag :type="row.grade_status==='DRAFT'?'warning':'success'" effect="light">{{ row.grade_status==='DRAFT'?'待发布':'已发布' }}</el-tag></template></el-table-column>
    <el-table-column label="操作" width="100"><template #default="{row}"><el-button v-permission="['ADMIN','TEACHER']" size="small" type="primary" link @click="handleGrade(row)">评分</el-button></template></el-table-column>
  </el-table>
</section>
</template>
<style scoped>.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.actions{display:flex;align-items:center}</style>
