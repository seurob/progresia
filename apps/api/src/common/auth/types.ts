import { Request } from "express";
import { Role } from "@prisma/client";

export interface JwtUser {
  sub: string;
  email: string;
  role: Role;
}

export interface AuthenticatedRequest extends Request {
  user: JwtUser;
}
