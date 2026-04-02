export interface User {
  oid: string;
  display_name: string;
  category: string;
  department: string;
  ad_roles: string[];
  clearance_level: number;
  domain: string;
  bound_policies: string[];
  employment_status: string;
}

export interface UsersResponse {
  users: User[];
}

export interface TokenResponse {
  jwt_token: string;
  oid: string;
  display_name: string;
  expires_in: number;
}
