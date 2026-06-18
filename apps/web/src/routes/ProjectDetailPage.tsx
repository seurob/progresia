import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FileText, Save } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import { z } from "zod";
import { FormField } from "../components/FormField";
import { api, getErrorMessage } from "../lib/api";
import { Project, Specification } from "../types/api";

const ideaSchema = z.object({
  problem: z.string().min(10),
  targetUsers: z.string().min(2),
  coreFeatures: z.string().min(2),
  complexity: z.string().min(2),
  needsAi: z.boolean(),
  needsAuth: z.boolean(),
  needsAdminPanel: z.boolean(),
  constraints: z.string().optional()
});

type IdeaForm = z.infer<typeof ideaSchema>;

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);
  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => (await api.get<Project>(`/projects/${projectId}`)).data,
    enabled: Boolean(projectId)
  });
  const form = useForm<IdeaForm>({
    resolver: zodResolver(ideaSchema),
    values: {
      problem: projectQuery.data?.idea?.problem ?? "",
      targetUsers: projectQuery.data?.idea?.targetUsers ?? "",
      coreFeatures: projectQuery.data?.idea?.coreFeatures?.join("\n") ?? "",
      complexity: projectQuery.data?.idea?.complexity ?? "standard",
      needsAi: projectQuery.data?.idea?.needsAi ?? false,
      needsAuth: projectQuery.data?.idea?.needsAuth ?? true,
      needsAdminPanel: projectQuery.data?.idea?.needsAdminPanel ?? true,
      constraints: projectQuery.data?.idea?.constraints ?? ""
    }
  });
  const saveIdea = useMutation({
    mutationFn: async (values: IdeaForm) =>
      api.post("/ideas", {
        projectId,
        problem: values.problem,
        targetUsers: values.targetUsers,
        coreFeatures: values.coreFeatures.split("\n").map((feature) => feature.trim()).filter(Boolean),
        complexity: values.complexity,
        needsAi: values.needsAi,
        needsAuth: values.needsAuth,
        needsAdminPanel: values.needsAdminPanel,
        constraints: values.constraints
      }),
    onSuccess: async () => {
      setServerError(null);
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (error) => setServerError(getErrorMessage(error))
  });
  const createSpec = useMutation({
    mutationFn: async () => {
      const project = projectQuery.data;
      return api.post<Specification>("/specifications", {
        projectId,
        type: "OPENSPEC",
        status: "GENERATED",
        content: {
          project: project?.name,
          sector: project?.sector,
          idea: project?.idea,
          generatedBy: "web-foundation"
        }
      });
    },
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
    onError: (error) => setServerError(getErrorMessage(error))
  });

  const project = projectQuery.data;

  if (projectQuery.isLoading) {
    return <p className="text-sm text-zinc-400">Cargando proyecto...</p>;
  }

  if (!project) {
    return <p className="text-sm text-rose-300">No se pudo cargar el proyecto.</p>;
  }

  return (
    <div className="grid gap-6">
      <Link className="subtle-link inline-flex w-fit" to="/">
        <ArrowLeft size={16} />
        Volver
      </Link>

      <section className="border-b border-white/10 pb-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-semibold uppercase text-emerald-300">{project.status}</p>
            <h1 className="mt-2 text-3xl font-semibold md:text-4xl">{project.name}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">{project.description}</p>
          </div>
          <button className="secondary-button" onClick={() => createSpec.mutate()} disabled={createSpec.isPending}>
            <FileText size={18} />
            {createSpec.isPending ? "Creando" : "Crear OpenSpec base"}
          </button>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="min-w-0 rounded-md border border-white/10 bg-white/[0.04] p-5">
          <h2 className="text-lg font-semibold">Idea wizard</h2>
          <form className="mt-5 grid gap-4" onSubmit={form.handleSubmit((values) => saveIdea.mutate(values))}>
            <FormField label="Problema" error={form.formState.errors.problem?.message}>
              <textarea className="input min-h-24" {...form.register("problem")} />
            </FormField>
            <FormField label="Usuarios objetivo" error={form.formState.errors.targetUsers?.message}>
              <input className="input" {...form.register("targetUsers")} />
            </FormField>
            <FormField label="Funcionalidades principales, una por linea" error={form.formState.errors.coreFeatures?.message}>
              <textarea className="input min-h-28" {...form.register("coreFeatures")} />
            </FormField>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Complejidad" error={form.formState.errors.complexity?.message}>
                <select className="input" {...form.register("complexity")}>
                  <option value="simple">Simple</option>
                  <option value="standard">Standard</option>
                  <option value="advanced">Advanced</option>
                </select>
              </FormField>
              <FormField label="Restricciones" error={form.formState.errors.constraints?.message}>
                <input className="input" {...form.register("constraints")} />
              </FormField>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <label className="check-row">
                <input type="checkbox" {...form.register("needsAuth")} />
                Auth
              </label>
              <label className="check-row">
                <input type="checkbox" {...form.register("needsAdminPanel")} />
                Admin
              </label>
              <label className="check-row">
                <input type="checkbox" {...form.register("needsAi")} />
                IA
              </label>
            </div>

            {serverError ? <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-200">{serverError}</p> : null}

            <button className="primary-button justify-center" type="submit" disabled={saveIdea.isPending}>
              <Save size={18} />
              {saveIdea.isPending ? "Guardando" : "Guardar idea"}
            </button>
          </form>
        </section>

        <section className="min-w-0 rounded-md border border-white/10 bg-white/[0.04] p-5">
          <h2 className="text-lg font-semibold">Specifications</h2>
          <div className="mt-5 grid gap-3">
            {(project.specifications ?? []).length === 0 ? (
              <p className="rounded-md border border-dashed border-white/15 p-5 text-sm text-zinc-400">
                Aun no hay specifications guardadas para este proyecto.
              </p>
            ) : (
              project.specifications?.map((specification) => (
                <article key={specification.id} className="min-w-0 rounded-md border border-white/10 bg-zinc-950/70 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium">{specification.type}</p>
                    <span className="status-pill">{specification.status}</span>
                  </div>
                  <pre className="mt-3 max-h-72 max-w-full overflow-auto rounded-md bg-black/30 p-3 text-xs leading-5 text-zinc-300">
                    {JSON.stringify(specification.content, null, 2)}
                  </pre>
                </article>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
