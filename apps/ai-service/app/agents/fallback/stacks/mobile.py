"""React Native + Expo + TypeScript + Expo Router + Zustand scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_mobile(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold de app móvil con React Native + Expo."""
    project_slug = slug(req.project_name)
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_camel_name = camel(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    entity_plural = pluralize(entity_slug_name)

    files: list[GeneratedFile] = [
        _package_json(project_slug),
        _tsconfig(),
        _app_json(project_slug, req.project_name),
        _root_layout(req.project_name),
        _tabs_layout(req.modules),
        _home_screen(req.project_name),
        _entity_list_screen(entity_pascal_name, entity_camel_name, entity_plural),
        _entity_detail_screen(entity_pascal_name, entity_camel_name, entity_slug_name),
        _entity_card(entity_pascal_name),
        _app_store(entity_pascal_name, entity_camel_name),
        _api_service(),
        _constants_config(),
        _types_index(req.modules, req.data_entities),
        _env_example(),
        _gitignore(),
        generate_readme(
            req,
            stack_summary="React Native · Expo · TypeScript · Expo Router · Zustand",
            prerequisites=[
                "Node.js 20 LTS — https://nodejs.org",
                "Expo CLI — npm install -g expo-cli",
                "Expo Go app (iOS/Android) — https://expo.dev/go",
            ],
            setup_commands=[
                "npm install",
                "npx expo start",
            ],
            env_vars=[
                ("EXPO_PUBLIC_API_URL", "http://localhost:3000"),
            ],
            api_port=19006,
        ),
    ]
    return files


def _package_json(project_slug: str) -> GeneratedFile:
    content = f"""\
{{
  "name": "{project_slug}",
  "version": "1.0.0",
  "main": "expo-router/entry",
  "scripts": {{
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  }},
  "dependencies": {{
    "@react-navigation/bottom-tabs": "^7.0.0",
    "@react-navigation/native": "^7.0.0",
    "axios": "^1.7.0",
    "expo": "~52.0.0",
    "expo-constants": "~17.0.0",
    "expo-font": "~13.0.0",
    "expo-router": "~4.0.0",
    "expo-splash-screen": "~0.29.0",
    "expo-status-bar": "~2.0.0",
    "react": "18.3.1",
    "react-native": "0.76.0",
    "zustand": "^5.0.0"
  }},
  "devDependencies": {{
    "@types/react": "~18.3.0",
    "typescript": "^5.7.0"
  }}
}}
"""
    return GeneratedFile(path="package.json", language="json", content=content)


def _tsconfig() -> GeneratedFile:
    content = """\
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["**/*.ts", "**/*.tsx", ".expo/types/**/*.d.ts", "expo-env.d.ts"]
}
"""
    return GeneratedFile(path="tsconfig.json", language="json", content=content)


def _app_json(project_slug: str, project_name: str) -> GeneratedFile:
    content = f"""\
{{
  "expo": {{
    "name": "{project_name}",
    "slug": "{project_slug}",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "automatic",
    "splash": {{
      "image": "./assets/splash-icon.png",
      "resizeMode": "contain",
      "backgroundColor": "#6366f1"
    }},
    "ios": {{
      "supportsTablet": true,
      "bundleIdentifier": "com.example.{project_slug.replace('-', '')}"
    }},
    "android": {{
      "adaptiveIcon": {{
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#6366f1"
      }},
      "package": "com.example.{project_slug.replace('-', '')}"
    }},
    "web": {{
      "bundler": "metro",
      "output": "static",
      "favicon": "./assets/favicon.png"
    }},
    "plugins": ["expo-router"],
    "experiments": {{
      "typedRoutes": true
    }}
  }}
}}
"""
    return GeneratedFile(path="app.json", language="json", content=content)


def _root_layout(project_name: str) -> GeneratedFile:
    content = f"""\
import {{ Stack }} from "expo-router";
import {{ StatusBar }} from "expo-status-bar";

// Layout raíz de la aplicación
export default function RootLayout() {{
  return (
    <>
      <Stack>
        <Stack.Screen name="(tabs)" options={{{{ headerShown: false }}}} />
      </Stack>
      <StatusBar style="auto" />
    </>
  );
}}
"""
    return GeneratedFile(path="app/_layout.tsx", language="typescript", content=content)


def _tabs_layout(modules: list[str]) -> GeneratedFile:
    content = """\
import { Tabs } from "expo-router";

// Navegador de pestañas principal
export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#6366f1",
        headerShown: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Inicio",
          tabBarLabel: "Inicio",
        }}
      />
      <Tabs.Screen
        name="items"
        options={{
          title: "Items",
          tabBarLabel: "Items",
        }}
      />
    </Tabs>
  );
}
"""
    return GeneratedFile(path="app/(tabs)/_layout.tsx", language="typescript", content=content)


def _home_screen(project_name: str) -> GeneratedFile:
    content = f"""\
import {{ View, Text, StyleSheet }} from "react-native";

// Pantalla de inicio
export default function HomeScreen() {{
  return (
    <View style={{styles.container}}>
      <Text style={{styles.title}}>{project_name}</Text>
      <Text style={{styles.subtitle}}>MVP generado con ProgresIA Studio</Text>
    </View>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
    backgroundColor: "#f9fafb",
  }},
  title: {{
    fontSize: 28,
    fontWeight: "bold",
    color: "#111827",
    marginBottom: 8,
    textAlign: "center",
  }},
  subtitle: {{
    fontSize: 16,
    color: "#6b7280",
    textAlign: "center",
  }},
}});
"""
    return GeneratedFile(path="app/(tabs)/index.tsx", language="typescript", content=content)


def _entity_list_screen(entity_pascal: str, entity_camel: str, entity_plural: str) -> GeneratedFile:
    content = f"""\
import {{ View, FlatList, Text, TouchableOpacity, StyleSheet, ActivityIndicator }} from "react-native";
import {{ useEffect }} from "react";
import {{ Link }} from "expo-router";
import {{ useAppStore }} from "@/store/useAppStore";
import {entity_pascal}Card from "@/components/{entity_pascal}Card";
import type {{ {entity_pascal} }} from "@/types";

// Pantalla de listado de {entity_pascal}
export default function {entity_pascal}sScreen() {{
  const {{ {entity_camel}s, loading, fetch{entity_pascal}s }} = useAppStore();

  useEffect(() => {{
    fetch{entity_pascal}s();
  }}, []);

  if (loading) {{
    return (
      <View style={{styles.centered}}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }}

  return (
    <View style={{styles.container}}>
      <FlatList
        data={{{entity_camel}s}}
        keyExtractor={{(item) => item.id}}
        renderItem={{({{ item }}) => <{entity_pascal}Card item={{item}} />}}
        contentContainerStyle={{styles.list}}
        ListEmptyComponent={{
          <View style={{styles.empty}}>
            <Text style={{styles.emptyText}}>No hay {entity_camel}s todavía</Text>
          </View>
        }}
      />
    </View>
  );
}}

const styles = StyleSheet.create({{
  container: {{ flex: 1, backgroundColor: "#f9fafb" }},
  list: {{ padding: 16, gap: 12 }},
  centered: {{ flex: 1, alignItems: "center", justifyContent: "center" }},
  empty: {{ flex: 1, alignItems: "center", paddingTop: 60 }},
  emptyText: {{ color: "#9ca3af", fontSize: 16 }},
}});
"""
    return GeneratedFile(path=f"app/(tabs)/{entity_plural}.tsx", language="typescript", content=content)


def _entity_detail_screen(entity_pascal: str, entity_camel: str, entity_slug: str) -> GeneratedFile:
    content = f"""\
import {{ View, Text, StyleSheet, ScrollView }} from "react-native";
import {{ useLocalSearchParams }} from "expo-router";

// Pantalla de detalle de {entity_pascal}
export default function {entity_pascal}DetailScreen() {{
  const {{ id }} = useLocalSearchParams<{{ id: string }}>();

  return (
    <ScrollView style={{styles.container}}>
      <View style={{styles.card}}>
        <Text style={{styles.label}}>ID</Text>
        <Text style={{styles.value}}>{{id}}</Text>
      </View>
    </ScrollView>
  );
}}

const styles = StyleSheet.create({{
  container: {{ flex: 1, backgroundColor: "#f9fafb" }},
  card: {{
    margin: 16,
    padding: 16,
    backgroundColor: "#fff",
    borderRadius: 12,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  }},
  label: {{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }},
  value: {{ fontSize: 16, color: "#111827" }},
}});
"""
    return GeneratedFile(path=f"app/{entity_slug}/[id].tsx", language="typescript", content=content)


def _entity_card(entity_pascal: str) -> GeneratedFile:
    content = f"""\
import {{ View, Text, StyleSheet, TouchableOpacity }} from "react-native";
import {{ Link }} from "expo-router";
import type {{ {entity_pascal} }} from "@/types";

interface Props {{
  item: {entity_pascal};
}}

// Tarjeta para mostrar un elemento en la lista
export default function {entity_pascal}Card({{ item }}: Props) {{
  return (
    <Link href={{`/{entity_pascal.lower()}/${{item.id}}`}} asChild>
      <TouchableOpacity style={{styles.card}}>
        <Text style={{styles.name}}>{{item.name}}</Text>
        {{item.description && (
          <Text style={{styles.description}}>{{item.description}}</Text>
        )}}
      </TouchableOpacity>
    </Link>
  );
}}

const styles = StyleSheet.create({{
  card: {{
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  }},
  name: {{ fontSize: 16, fontWeight: "600", color: "#111827" }},
  description: {{ fontSize: 14, color: "#6b7280", marginTop: 4 }},
}});
"""
    return GeneratedFile(path=f"components/{entity_pascal}Card.tsx", language="typescript", content=content)


def _app_store(entity_pascal: str, entity_camel: str) -> GeneratedFile:
    content = f"""\
import {{ create }} from "zustand";
import {{ apiService }} from "@/services/api";
import type {{ {entity_pascal} }} from "@/types";

// Estado global con Zustand
interface AppState {{
  {entity_camel}s: {entity_pascal}[];
  loading: boolean;
  error: string | null;
  fetch{entity_pascal}s: () => Promise<void>;
}}

export const useAppStore = create<AppState>((set) => ({{
  {entity_camel}s: [],
  loading: false,
  error: null,

  fetch{entity_pascal}s: async () => {{
    set({{ loading: true, error: null }});
    try {{
      const data = await apiService.get<{entity_pascal}[]>("/{entity_camel}s");
      set({{ {entity_camel}s: data, loading: false }});
    }} catch (err) {{
      set({{ loading: false, error: "No se pudieron cargar los datos" }});
    }}
  }},
}}));
"""
    return GeneratedFile(path="store/useAppStore.ts", language="typescript", content=content)


def _api_service() -> GeneratedFile:
    content = """\
import axios from "axios";
import Constants from "expo-constants";

// URL de la API — configurada en app.json o .env
const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  Constants.expoConfig?.extra?.apiUrl ??
  "http://localhost:3000";

const client = axios.create({
  baseURL: API_URL + "/api",
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

export const apiService = {
  get: <T>(url: string) => client.get<T>(url).then((r) => r.data),
  post: <T>(url: string, data: unknown) =>
    client.post<T>(url, data).then((r) => r.data),
  put: <T>(url: string, data: unknown) =>
    client.put<T>(url, data).then((r) => r.data),
  delete: (url: string) => client.delete(url).then((r) => r.data),
};
"""
    return GeneratedFile(path="services/api.ts", language="typescript", content=content)


def _constants_config() -> GeneratedFile:
    content = """\
// Constantes de configuración de la aplicación
export const Config = {
  API_URL: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:3000",
  APP_VERSION: "1.0.0",
} as const;
"""
    return GeneratedFile(path="constants/Config.ts", language="typescript", content=content)


def _types_index(modules: list[str], data_entities: list[dict]) -> GeneratedFile:
    if data_entities:
        type_blocks = [
            f"""\
export interface {pascal(e.get("name", "Item"))} {{
  id: string;
  name: string;
  description?: string | null;
  createdAt: string;
}}"""
            for e in data_entities[:6]
        ]
    else:
        type_blocks = [
            f"""\
export interface {pascal(m)} {{
  id: string;
  name: string;
  description?: string | null;
  createdAt: string;
}}"""
            for m in modules[:4]
        ]

    content = "\n\n".join(type_blocks) + "\n"
    return GeneratedFile(path="types/index.ts", language="typescript", content=content)


def _env_example() -> GeneratedFile:
    content = """\
# URL del backend API (accesible desde el dispositivo)
EXPO_PUBLIC_API_URL=http://localhost:3000
"""
    return GeneratedFile(path=".env.example", language="env", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
node_modules/
.expo/
dist/
web-build/
.env
.env.local
*.log
.DS_Store
"""
    return GeneratedFile(path=".gitignore", language="gitignore", content=content)
