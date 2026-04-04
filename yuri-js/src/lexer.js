const T_REGEX = /(#\[\[[^\]]*\]\])|(\[\[[^\]]*\]\])|(@\w+)|("(?:[^"]*)")|(\d+)|([=:+\-*/><!]+)|(\w+\.\w+)|(\w+)/g;

export function getIndentLevel(line) {
  return line.length - line.trimStart().length;
}

export function tokenize(line) {
  const commentMatch = line.match(/\?\s*\(.*\)/);
  if (commentMatch) {
    line = line.slice(0, commentMatch.index);
  }

  if (!line.trim()) return [];

  return Array.from(line.matchAll(T_REGEX), m => m[0]);
}
