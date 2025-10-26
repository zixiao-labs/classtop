<template>
    <mdui-layout>
        <mdui-layout-main class="home">
            <div class="content">
                <transition name="fade">
                    <keep-alive>
                        <router-view></router-view>
                    </keep-alive>
                </transition>
            </div>
        </mdui-layout-main>
        <mdui-navigation-bar :value="selectedItem" @change="routeTo($event.target.value)" style="position: relative">
            <mdui-navigation-bar-item v-for="item in items" :key="item.value" :icon="item.icon" :value="item.value">
                {{ item.label }}
            </mdui-navigation-bar-item>
        </mdui-navigation-bar>
    </mdui-layout>
</template>

<script setup>
import { ref } from 'vue';
import router from './router';



const items = [
    { icon: 'home', value: '/', label: '主页' },
    { icon: 'class', value: '/schedule', label: '课程表' },
    { icon: 'graphic_eq', value: '/audio', label: '音量监控' },
    { icon: 'settings', value: '/settings', label: '设置' },
];
const selectedItem = ref(items[0].value);

const routeTo = (value) => {
    selectedItem.value = value;
    router.push(value);
}
</script>

<style scoped>
.page {
    padding: 16px;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity var(--mdui-motion-duration-medium3) var(--mdui-motion-easing-emphasized);
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.home {
    display: flex;
    justify-content: left;
    align-items: start;
    height: 100%;
}

.content {
    flex: 1;
    overflow: auto;
    height: 100%;
    width: 100%;
    padding: 1rem;
}

mdui-layout {
    height: 100%;
}
</style>
