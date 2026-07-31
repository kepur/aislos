<template>
  <div class="space-y-4 p-4">
    <div class="flex justify-between">
      <h1 class="text-xl font-bold text-slate-800">供应目录</h1>
      <button class="text-sm font-semibold text-blue-600" @click="start()">Add</button>
    </div>
    <form v-if="editing" class="m-card space-y-3" @submit.prevent="save">
      <input v-model="form.title" class="m-input" required placeholder="Title"/>
      <select v-model="form.category_schema_id" class="m-input">
        <option value="">Category</option>
        <option v-for="x in categories" :key="x.id" :value="x.id">{{ x.name }}</option>
      </select>
      <input v-model.number="price" class="m-input" type="number" step="0.01" min="0" placeholder="Price"/>
      <select v-model="form.status" class="m-input">
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
        <option value="draft">Draft</option>
      </select>
      <button class="m-btn-primary">{{ form.id?'Save':'Create' }}</button>
      <button type="button" class="m-card w-full text-sm" @click="editing=false">Cancel</button>
    </form>
    <div v-for="item in items" :key="item.id" class="m-card">
      <p class="font-semibold text-slate-800">{{ item.title }}</p>
      <p class="text-xs text-slate-400">{{ item.status }} · {{ money(item.price_minor,item.currency) }}</p>
      <div class="mt-3 flex gap-4">
        <button class="text-xs font-semibold text-blue-600" @click="start(item)">Edit</button>
        <button class="text-xs font-semibold text-red-500" @click="archive(item.id)">Archive</button>
      </div>
    </div>
    <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
  </div>
</template>
<script setup lang="ts">definePageMeta({middleware:['auth']});const api=useCommerce();const items=ref<any[]>([]);const categories=ref<any[]>([]);const editing=ref(false);const price=ref(0);const error=ref('');const form=reactive<any>({id:'',title:'',category_schema_id:'',status:'active',currency:'EUR'});const money=(v:number|null,c='EUR')=>v==null?'—':new Intl.NumberFormat(undefined,{style:'currency',currency:c}).format(v/100);async function load(){items.value=(await api.listSupplierListings()).items;categories.value=(await api.listPublicCategories()).items}function start(x?:any){Object.assign(form,x||{id:'',title:'',category_schema_id:'',status:'active',currency:'EUR'});price.value=(x?.price_minor||0)/100;editing.value=true}async function save(){try{const body={title:form.title,category_schema_id:form.category_schema_id||null,status:form.status,currency:form.currency,price_minor:Math.round(price.value*100)};form.id?await api.updateSupplierListing(form.id,body):await api.createSupplierListing(body);editing.value=false;await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}async function archive(id:string){await api.archiveSupplierListing(id);await load()}onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))</script>
