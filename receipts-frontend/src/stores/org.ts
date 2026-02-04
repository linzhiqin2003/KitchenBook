import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/client";

export interface OrgInfo {
  id: string;
  name: string;
  member_count: number;
  created_at: string;
}

export interface OrgMember {
  id: number;
  role: string;
  joined_at: string;
  nickname: string;
  email: string;
  avatar_display?: string;
}

export interface InviteInfo {
  id: string;
  org: string;
  org_name: string;
  expires_at: string | null;
  max_uses: number;
  use_count: number;
  is_active: boolean;
  created_at: string;
}

export const useOrgStore = defineStore("org", () => {
  const orgs = ref<OrgInfo[]>([]);
  const members = ref<OrgMember[]>([]);

  async function fetchOrgs() {
    const { data } = await api.get("/auth/orgs/");
    orgs.value = data;
    return data;
  }

  async function createOrg(name: string) {
    const { data } = await api.post("/auth/orgs/", { name });
    orgs.value.unshift(data);
    return data;
  }

  async function fetchMembers(orgId: string) {
    const { data } = await api.get(`/auth/orgs/${orgId}/members/`);
    members.value = data;
    return data;
  }

  async function createInvite(orgId: string, options?: { expires_at?: string; max_uses?: number }) {
    const { data } = await api.post(`/auth/orgs/${orgId}/invite/`, options || {});
    return data as InviteInfo;
  }

  async function getInviteInfo(inviteId: string) {
    const { data } = await api.get(`/auth/invite/${inviteId}/accept/`);
    return data;
  }

  async function acceptInvite(inviteId: string) {
    const { data } = await api.post(`/auth/invite/${inviteId}/accept/`);
    return data;
  }

  async function leaveOrg(orgId: string) {
    const { data } = await api.post(`/auth/orgs/${orgId}/leave/`);
    orgs.value = orgs.value.filter((o) => o.id !== orgId);
    return data;
  }

  async function removeMember(orgId: string, memberId: number) {
    const { data } = await api.post(`/auth/orgs/${orgId}/members/${memberId}/remove/`);
    return data;
  }

  async function dissolveOrg(orgId: string) {
    const { data } = await api.delete(`/auth/orgs/${orgId}/`);
    orgs.value = orgs.value.filter((o) => o.id !== orgId);
    return data;
  }

  return {
    orgs,
    members,
    fetchOrgs,
    createOrg,
    fetchMembers,
    createInvite,
    getInviteInfo,
    acceptInvite,
    leaveOrg,
    removeMember,
    dissolveOrg,
  };
});
