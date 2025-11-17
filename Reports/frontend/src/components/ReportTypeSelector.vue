<template>
  <div class="report-type-selector">
    <div class="selector-header">
      <span class="label">选择报告类型：</span>
    </div>
    <div class="type-buttons">
      <el-radio-group v-model="selectedType" @change="handleChange">
        <el-radio-button
          v-for="(typeInfo, typeKey) in reportTypes"
          :key="typeKey"
          :label="typeKey"
          class="type-radio"
        >
          {{ typeInfo.name }}
        </el-radio-button>
      </el-radio-group>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 报告类型配置
const reportTypes = {
  'strategy': { name: '策略报告' },
  'industry': { name: '行业研报' },
  'macro': { name: '宏观研究' },
  'stock': { name: '个股研报' }
}

// 单选模式：只存储一个类型
const selectedType = ref('strategy')  // 默认选中第一个类型
const previousType = ref('strategy')  // 记录上一次选中的类型，用于判断是否重复点击
const limit = 6  // 固定数量为6

const emit = defineEmits(['change', 'type-selected', 'refresh'])

// 类型变化
const handleChange = () => {
  if (!selectedType.value) return
  
  // 如果是同一个类型，不触发刷新（避免重复请求）
  if (selectedType.value === previousType.value) {
    return
  }
  
  // 更新上一次选中的类型
  previousType.value = selectedType.value
  
  emit('change', {
    types: [selectedType.value],  // 转换为数组格式以兼容现有逻辑
    limit: limit
  })
  
  // 触发联动：通知父组件类型变化（传递数组格式）
  emit('type-selected', [selectedType.value])
  
  // 触发普通刷新（使用缓存）
  emit('refresh', {
    types: [selectedType.value],
    limit: limit,
    force: false
  })
}

// 组件挂载时触发一次联动和刷新
onMounted(() => {
  // 延迟触发，确保父组件已准备好
  setTimeout(() => {
    emit('type-selected', [selectedType.value])
    // 初始化时也触发一次刷新
    emit('refresh', {
      types: [selectedType.value],
      limit: limit,
      force: false
    })
  }, 100)
})

// 暴露方法供父组件调用
defineExpose({
  getSelectedTypes: () => selectedType.value ? [selectedType.value] : [],
  getLimit: () => limit,
  setSelectedTypes: (types) => {
    // 如果传入数组，取第一个；如果传入字符串，直接使用
    let newType = null
    if (Array.isArray(types) && types.length > 0) {
      newType = types[0]
    } else if (typeof types === 'string') {
      newType = types
    }
    
    if (newType && newType !== selectedType.value) {
      // 更新上一次选中的类型
      previousType.value = selectedType.value
      selectedType.value = newType
      handleChange()
    }
  }
})
</script>

<style scoped>
.report-type-selector {
  padding: 16px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.type-buttons {
  margin-bottom: 0;
}

.type-buttons :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.type-buttons :deep(.el-radio-button) {
  margin: 0;
}

.type-buttons :deep(.el-radio-button__inner) {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.3s;
}

.type-buttons :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: #667eea;
  border-color: #667eea;
  color: white;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.type-buttons :deep(.el-radio-button:not(.is-active) .el-radio-button__inner) {
  background-color: #f5f7fa;
  border-color: #dcdfe6;
  color: #606266;
}

.type-buttons :deep(.el-radio-button:not(.is-active) .el-radio-button__inner:hover) {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}
</style>

