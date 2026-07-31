# Verification Risk Register
Generated at: 2026-06-13T06:56:30.367984+00:00

These findings block the affected capability from VERIFIED until an independent verifier confirms the risk is removed or explicitly accepted.

## Source Capability Risks

| Source | Capability | Risk Flags | Status |
|---|---|---|---|
| CebuProjects/h5-frontend/pages/buyer/offers.vue | /buyer/offers | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/offers.vue | exception_flow:/buyer/offers:L103:}).catch(() => isDemoToken(authStore.accessToken) ? demoOffersForIntent(intent.id) : [] as Offer[]) | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/offers.vue | state_machine:/buyer/offers:L35:<div class="card border" :class="offer.status === 'AWARDED' ? 'border-green-300' : 'border-transpare | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/offers.vue | state_machine:/buyer/offers:L85:function getOfferBadgeClass(status: string) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | /buyer/requests/:id | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | exception_flow:/buyer/requests/:id:L347:} catch { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | exception_flow:/buyer/requests/:id:L397:} catch (e: any) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | exception_flow:/buyer/requests/:id:L398:showToast({ type: "fail", message: e?.data?.detail || "Bind failed" }) | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | exception_flow:/buyer/requests/:id:L420:} catch { /* user cancelled */ } | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L113:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L114:@keyup | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L160:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L164:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L173:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L182:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L212:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L269:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L5:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | operation:/buyer/requests/:id:L79:@change | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L242::class="offer.status === 'AWARDED' ? 'border-green-300 bg-green-50' : 'border-transparent'"> | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L244:<div v-if="offer.status === 'AWARDED'" class="text-xs text-green-700 font-bold mb-2 flex items-cente | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L267:v-if="intent.status === 'ACTIVE' && offer.status !== 'AWARDED'" | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L274:v-if="offer.status === 'AWARDED'" | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L314:{ id: 'mo1', total_price_minor: 24500000, unit_price_minor: 49000, currency: 'PHP', qty_available: 6 | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L315:{ id: 'mo2', total_price_minor: 22000000, unit_price_minor: 44000, currency: 'PHP', qty_available: 5 | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L316:{ id: 'mo3', total_price_minor: 26000000, unit_price_minor: 52000, currency: 'PHP', qty_available: 1 | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L402:function getIntentBadgeClass(status: string) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/buyer/requests/[id].vue | state_machine:/buyer/requests/:id:L407:function getOfferBadgeClass(status: string) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | /marketplace/:id | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L361:} catch {} | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L417:} catch (e: any) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L418:rfqError.value = e?.data?.detail || 'Failed to submit. Please try again.' | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L441:} catch (e: any) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L442:buyError.value = e?.data?.detail || 'Order failed. Please try again.' | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L456:} catch { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L108:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L115:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L120:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L130:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L135:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L161:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L175:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L18:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L198:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L212:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L217:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L234:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L238:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L250:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L269:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L38:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | /marketplace | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | exception_flow:/marketplace:L242:} catch {} | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | exception_flow:/marketplace:L267:} catch (e) { | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | exception_flow:/marketplace:L268:console.error(e) | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L128:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L129:@keyup | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L12:@keyup | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L15:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L163:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L174:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L27:@update:modelValue | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L36:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L42:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L56:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L62:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L74:@click | static_demo_data_dependency | TODO |
| CebuProjects/h5-frontend/pages/marketplace/index.vue | operation:/marketplace:L81:@change | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | /buyer/requests/:id | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L297:const { data, error } = await api.getIntent(id) | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L305:console.error(error) | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L306:useToast().add({ title: 'Error fetching request details', color: 'red' }) | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L325:} catch { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L352:} catch { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L384:} catch (e: any) { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | exception_flow:/buyer/requests/:id:L385:useToast().add({ title: e?.data?.detail || 'Bind failed', color: 'red' }) | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L104:@change | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L131:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L132:@keyup | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L204:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L207:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L210:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L213:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L222:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L230:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | operation:/buyer/requests/:id:L263:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | state_machine:/buyer/requests/:id:L393:const getStatusColor = (status: string) => { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/buyer/requests/[id]/index.vue | state_machine:/buyer/requests/:id:L8:<UBadge :color="getStatusColor(intent.status)" variant="subtle">{{ intent.status }}</UBadge> | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | /marketplace/:id | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L402:} catch (e) { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L403:console.error('Product load error', e) | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L439:} catch { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L518:} catch (e: any) { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L519:rfqError.value = e?.data?.detail || 'Failed to submit. Please try again.' | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L543:} catch (e: any) { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | exception_flow:/marketplace/:id:L544:buyError.value = e?.data?.detail || 'Order failed. Please try again.' | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L101:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L108:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L115:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L140:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L167:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L184:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L204:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L207:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L226:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L228:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L242:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L262:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L265:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L36:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/[id].vue | operation:/marketplace/:id:L93:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | /marketplace | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | exception_flow:/marketplace:L260:} catch {} | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | exception_flow:/marketplace:L291:} catch (e) { | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | exception_flow:/marketplace:L292:console.error('Feed error', e) | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L120:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L172:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L184:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L21:@keyup | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L25:@change | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L32:@change | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L40:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L54:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L62:@click | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L72:@change | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L81:@change | static_demo_data_dependency | TODO |
| CebuProjects/pc-frontend/pages/marketplace/index.vue | operation:/marketplace:L90:@change | static_demo_data_dependency | TODO |

## Test Quality Risks

| Source | Line | Risk | Detail | Required Action |
|---|---:|---|---|---|
| — | — | none detected | — | — |
