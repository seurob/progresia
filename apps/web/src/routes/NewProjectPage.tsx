import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router";
import { z } from "zod";
import { FormField } from "../components/FormField";
import { api, getErrorMessage } from "../lib/api";
import { Project, Workspace } from "../types/api";

const projectSchema = z.object({
  workspaceId: z.string().min(1),
  name: z.string().min(2),
  sector: z.string().min(2),
  productType: z.string().min(2),
  description: z.string().min(10)
});

type ProjectForm = z.infer<typeof projectSchema>;

export function NewProjectPage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => (await api.get<Workspace[]>("/workspaces")).data
  });
  const form = useForm<ProjectForm>({
    resolver: zodResolver(projectSchema),
    values: {
      workspaceId: workspacesQuery.data?.[0]?.id ?? "",
      name: "",
      sector: "",
      productType: "SaaS operativo",
      description: ""
    }
  });
  const mutation = useMutation({
    mutationFn: async (values: ProjectForm) => (await api.post<Project>("/projects", values)).data,
    onSuccess: (project) => navigate(`/projects/${project.id}`),
    onError: (error) => setServerError(getErrorMessage(error))
  });

  return (
    <div className="mx-auto max-w-3xl">
      <Link className="subtle-link mb-5 inline-flex" to="/">
        <ArrowLeft size={16} />
        Volver
      </Link>
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase text-emerald-300">Nuevo proyecto</p>
        <h1 className="mt-2 text-3xl font-semibold">Define el contenedor del MVP</h1>
      </div>

      <form className="grid gap-5 rounded-md border border-white/10 bg-white/[0.04] p-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
        <FormField label="Workspace" error={form.formState.errors.workspaceId?.message}>
          <select className="input" {...form.register("workspaceId")} disabled={workspacesQuery.isLoading}>
            {(workspacesQuery.data ?? []).map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Nombre" error={form.formState.errors.name?.message}>
          <input className="input" {...form.register("name")} placeholder="Reservas de clases particulares" />
        </FormField>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Sector" error={form.formState.errors.sector?.message}>
            <input className="input" {...form.register("sector")} placeholder="Educacion" />
          </FormField>
          <FormField label="Tipo de producto" error={form.formState.errors.productType?.message}>
            <input className="input" {...form.register("productType")} />
          </FormField>
        </div>
        <FormField label="Descripcion" error={form.formState.errors.description?.message}>
          <textarea className="input min-h-28 resize-y" {...form.register("description")} placeholder="Plataforma para gestionar profesores, alumnos, clases y reservas." />
        </FormField>

        {serverError ? <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-200">{serverError}</p> : null}

        <button className="primary-button justify-center" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Creando" : "Crear proyecto"}
          <ArrowRight size={18} />
        </button>
      </form>
    </div>
  );
}
