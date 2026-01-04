<template>
  <el-row :gutter="20" class="card-list">
    <el-col v-for="(item, index) in dataList" :key="index" :sm="12" :md="6" :lg="6">
      <div class="card art-custom-card">
        <span class="des subtitle">{{ item.des }}</span>
        <ArtCountTo class="number box-title" :target="item.num" :duration="1300" />
        <div class="change-box">
          <span class="change-text">较上周</span>
          <span
            class="change"
            :class="[item.change.indexOf('+') === -1 ? 'text-danger' : 'text-success']"
          >
            {{ item.change }}
          </span>
        </div>
        <i class="iconfont-sys" v-html="item.icon"></i>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
  import { reactive } from 'vue'

  const dataList = reactive([
    {
      des: 'HTS版本总数',
      icon: '&#xe726;',
      startVal: 0,
      duration: 1000,
      num: 25,
      change: '+5%'
    },
    {
      des: 'Code查询总量',
      icon: '&#xe721;',
      startVal: 0,
      duration: 1000,
      num: 15820,
      change: '+18%'
    },
    {
      des: '编码总数',
      icon: '&#xe742;',
      startVal: 0,
      duration: 1000,
      num: 98520,
      change: '+3%'
    },
    {
      des: '活跃用户',
      icon: '&#xe608;',
      startVal: 0,
      duration: 1000,
      num: 286,
      change: '+12%'
    }
  ])
</script>

<style lang="scss" scoped>
  .card-list {
    box-sizing: border-box;
    display: flex;
    flex-wrap: wrap;
    background-color: transparent !important;

    .art-custom-card {
      position: relative;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      justify-content: center;
      width: 100%;
      height: 140px;
      padding: 0 18px;
      list-style: none;
      transition: all 0.3s ease;

      $icon-size: 52px;

      .iconfont-sys {
        position: absolute;
        top: 0;
        right: 20px;
        bottom: 0;
        width: $icon-size;
        height: $icon-size;
        margin: auto;
        overflow: hidden;
        font-size: 22px;
        line-height: $icon-size;
        color: var(--el-color-primary) !important;
        text-align: center;
        background-color: var(--el-color-primary-light-9);
        border-radius: 12px;
      }

      .des {
        display: block;
        height: 14px;
        font-size: 14px;
        line-height: 14px;
      }

      .number {
        display: block;
        margin-top: 10px;
        font-size: 28px;
        font-weight: 400;
      }

      .change-box {
        display: flex;
        align-items: center;
        margin-top: 10px;

        .change-text {
          display: block;
          font-size: 13px;
          color: var(--art-text-gray-600);
        }

        .change {
          display: block;
          margin-left: 5px;
          font-size: 13px;
          font-weight: bold;

          &.text-success {
            color: var(--el-color-success);
          }

          &.text-danger {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }

  .dark {
    .card-list {
      .art-custom-card {
        .iconfont-sys {
          background-color: #232323 !important;
        }
      }
    }
  }
</style>
