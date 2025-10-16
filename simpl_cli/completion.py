#!/usr/bin/env python3
import os
import glob
import stat
import pwd
import grp
import shlex
import subprocess
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from prompt_toolkit.completion import FuzzyWordCompleter, Completer, Completion
from prompt_toolkit.document import Document
from .config import Config


class FileMetadata:
    
    def __init__(self):
        self._metadata_cache = {}
    
    def get_file_info(self, file_path: str) -> str:

        if file_path in self._metadata_cache:
            return self._metadata_cache[file_path]
        
        try:
            stat_info = os.stat(file_path)
            
            if os.path.isdir(file_path):
                file_type = " Directory"
            elif os.path.islink(file_path):
                file_type = " Symlink"
            elif os.access(file_path, os.X_OK):
                file_type = " Executable"
            else:
                _, ext = os.path.splitext(file_path)
                file_type = self._get_file_type_by_extension(ext.lower())
            
            size = stat_info.st_size
            size_str = self._format_size(size)
            
            perms = stat.filemode(stat_info.st_mode)
            
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
                group = grp.getgrgid(stat_info.st_gid).gr_name
            except (KeyError, OSError):
                owner = str(stat_info.st_uid)
                group = str(stat_info.st_gid)
            
            mtime = datetime.fromtimestamp(stat_info.st_mtime)
            mtime_str = mtime.strftime("%Y-%m-%d %H:%M")
            
            meta_info = f"{file_type} | {size_str} | {perms} | {owner}:{group} | {mtime_str}"
            
            self._metadata_cache[file_path] = meta_info
            return meta_info
            
        except (OSError, PermissionError, FileNotFoundError):
            return " Access denied or file not found"
    
    def _get_file_type_by_extension(self, ext: str) -> str:
        type_map = {
            '.py': ' Python',
            '.js': ' JavaScript',
            '.ts': ' TypeScript',
            '.html': ' HTML',
            '.css': ' CSS',
            '.json': ' JSON',
            '.xml': ' XML',
            '.yaml': ' YAML',
            '.yml': ' YAML',
            '.md': ' Markdown',
            '.txt': ' Text',
            '.log': ' Log',
            '.conf': ' Config',
            '.cfg': ' Config',
            '.ini': ' Config',
            '.sh': ' Shell Script',
            '.bash': ' Bash Script',
            '.zsh': ' Zsh Script',
            '.fish': ' Fish Script',
            '.jpg': ' JPEG Image',
            '.jpeg': ' JPEG Image',
            '.png': ' PNG Image',
            '.gif': ' GIF Image',
            '.svg': ' SVG Image',
            '.pdf': ' PDF',
            '.doc': ' Word Doc',
            '.docx': ' Word Doc',
            '.xls': ' Excel',
            '.xlsx': ' Excel',
            '.zip': ' ZIP Archive',
            '.tar': ' TAR Archive',
            '.gz': ' GZip Archive',
            '.rar': ' RAR Archive',
            '.7z': ' 7Z Archive',
            '.mp3': ' MP3 Audio',
            '.mp4': ' MP4 Video',
            '.avi': ' AVI Video',
            '.mov': ' MOV Video',
            '.wav': ' WAV Audio',
            '.flac': ' FLAC Audio',
        }
        
        return type_map.get(ext, ' File')
    
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        if i == 0:  # Bytes
            return f"{int(size)} {size_names[i]}"
        else:
            return f"{size:.1f} {size_names[i]}"
    
    def clear_cache(self):
        self._metadata_cache.clear()


class PathScanner:
    
    DIR_COMMANDS = {'cd', 'pushd', 'popd', 'rmdir'}
    
    FILE_COMMANDS = {'cat', 'less', 'more', 'head', 'tail', 'vim', 'nano', 'code', 'subl', 'gedit'}
    
    BOTH_COMMANDS = {'ls', 'll', 'la', 'cp', 'mv', 'rm', 'chmod', 'chown', 'stat', 'file', 'du', 'find'}
    
    def __init__(self):
        self._cache = {}
        self._cache_time = {}
        self.metadata = FileMetadata()
        
    def _get_cache_key(self, path: str) -> str:
        try:
            mtime = os.path.getmtime(path) if os.path.exists(path) else 0
            return f"{path}:{mtime}"
        except OSError:
            return f"{path}:0"
    
    def _is_cache_valid(self, path: str) -> bool:
        cache_key = self._get_cache_key(path)
        return cache_key in self._cache
    
    def scan_directory(self, path: str = None, include_hidden: bool = False) -> Tuple[Dict[str, List[str]], Dict[str, str]]:

        if path is None:
            path = os.getcwd()
            
        cache_key = self._get_cache_key(path)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        files = []
        directories = []
        meta_dict = {}
        
        try:
            for item in os.listdir(path):
                if not include_hidden and item.startswith('.'):
                    continue
                    
                item_path = os.path.join(path, item)
                
                meta_info = self.metadata.get_file_info(item_path)
                meta_dict[item] = meta_info
                
                if os.path.isdir(item_path):
                    directories.append(item)
                elif os.path.isfile(item_path):
                    files.append(item)
                    
        except (PermissionError, FileNotFoundError):
            pass
        
        result = (
            {
                'files': sorted(files),
                'directories': sorted(directories)
            },
            meta_dict
        )
        
        self._cache[cache_key] = result
        return result
    
    def get_completions_for_command(self, command: str, path: str = None) -> Tuple[List[str], Dict[str, str]]:
        scan_result, meta_dict = self.scan_directory(path)
        
        if command in self.DIR_COMMANDS:
            items = scan_result['directories']
        elif command in self.FILE_COMMANDS:
            items = scan_result['files'] + scan_result['directories']
        else:
            items = scan_result['files'] + scan_result['directories']
        
        filtered_meta = {item: meta_dict[item] for item in items if item in meta_dict}
        
        return items, filtered_meta


class CommandParser:
    
    def __init__(self):
        self.scanner = PathScanner()
    
    def parse_input(self, text: str) -> Dict[str, any]:
        """
        Parse input text and return completion context
        Returns: {
            'command': str,
            'args': List[str], 
            'current_arg': str,
            'completion_type': str,  # 'path', 'command', 'none'
            'target_directory': str
        }
        """
        if not text.strip():
            return {
                'command': '',
                'args': [],
                'current_arg': '',
                'completion_type': 'command',
                'target_directory': os.getcwd()
            }
        
        parts = text.split()
        command = parts[0] if parts else ''
        args = parts[1:] if len(parts) > 1 else []
        
        if len(parts) == 1 and not text.endswith(' '):
            completion_type = 'command'
            current_arg = command
        else:
            completion_type = 'path'
            if text.endswith(' '):
                current_arg = ''
            else:
                current_arg = args[-1] if args else ''
        
        target_directory = os.getcwd()
        
        if current_arg and ('/' in current_arg or '\\' in current_arg):
            dir_part = os.path.dirname(current_arg)
            if dir_part:
                potential_dir = os.path.join(os.getcwd(), dir_part)
                if os.path.isdir(potential_dir):
                    target_directory = potential_dir
        
        return {
            'command': command,
            'args': args,
            'current_arg': current_arg,
            'completion_type': completion_type,
            'target_directory': target_directory
        }


class DynamicPathCompleter(Completer):
    
    def __init__(self):
        self.parser = CommandParser()
        self.scanner = PathScanner()
        
        base_shell_commands = [
            'ls', 'cd', 'pwd', 'cat', 'less', 'more', 'head', 'tail',
            'cp', 'mv', 'rm', 'mkdir', 'rmdir', 'chmod', 'chown',
            'find', 'grep', 'awk', 'sed', 'sort', 'uniq', 'wc',
            'ps', 'kill', 'jobs', 'bg', 'fg', 'top', 'htop',
            'vim', 'nano', 'code', 'git', 'python', 'pip','source',
            'clear', 'history', 'exit', 'which', 'whereis'
        ]
        self.shell_commands = self._load_all_commands(base_shell_commands)
        
        self.command_meta = {
            'ls': ' List directory contents',
            'cd': ' Change directory',
            'pwd': ' Print working directory',
            'cat': ' Display file contents',
            'less': ' View file with paging',
            'more': ' View file with paging',
            'head': ' Display first lines of file',
            'tail': ' Display last lines of file',
            'cp': ' Copy files or directories',
            'mv': ' Move/rename files or directories',
            'rm': ' Remove files or directories',
            'mkdir': ' Create directory',
            'rmdir': ' Remove empty directory',
            'chmod': ' Change file permissions',
            'chown': ' Change file ownership',
            'find': ' Search for files and directories',
            'grep': ' Search text patterns in files',
            'vim': ' Vi/Vim text editor',
            'nano': ' Nano text editor',
            'code': ' VS Code editor',
            'git': ' Git version control',
            'python': ' Python interpreter',
            'pip': ' Python package installer'
        }
        self.bash_completion_runner = BashCompletionRunner()
        
    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        context = self.parser.parse_input(text)
        
        if context['completion_type'] == 'command':
            fuzzy_completer = FuzzyWordCompleter(
                words=self.shell_commands,
                meta_dict=self.command_meta
            )
            
            for completion in fuzzy_completer.get_completions(document, complete_event):
                yield completion
        
        elif context['completion_type'] == 'path':
            command = context['command']
            current_arg = context['current_arg']
            target_dir = context['target_directory']
            
            bash_matches = self.bash_completion_runner.get_completions(text, document.cursor_position)
            if bash_matches:
                for match in bash_matches:
                    yield match
                return

            candidates, meta_dict = self.scanner.get_completions_for_command(command, target_dir)
            
            if candidates:
                if current_arg and ('/' in current_arg or '\\' in current_arg):
                    dir_part = os.path.dirname(current_arg)
                    file_part = os.path.basename(current_arg)
                    
                    filtered_candidates = []
                    filtered_meta = {}

                    for candidate in candidates:
                        if candidate.lower().startswith(file_part.lower()) or self._fuzzy_match(candidate, file_part):
                            filtered_candidates.append(candidate)
                            if candidate in meta_dict:
                                filtered_meta[candidate] = meta_dict[candidate]

                    if filtered_candidates:
                        fuzzy_completer = FuzzyWordCompleter(
                            words=filtered_candidates,
                            meta_dict=filtered_meta
                        )

                        partial_doc = Document(file_part, len(file_part))
                        start_offset = -len(file_part)

                        for completion in fuzzy_completer.get_completions(partial_doc, complete_event):
                            yield Completion(
                                text=completion.text,
                                start_position=start_offset,
                                display=completion.display,
                                display_meta=completion.display_meta,
                            )
                else:
                    fuzzy_completer = FuzzyWordCompleter(
                        words=candidates,
                        meta_dict=meta_dict
                    )
                    
                    arg_doc = Document(current_arg, len(current_arg))
                    
                    for completion in fuzzy_completer.get_completions(arg_doc, complete_event):
                        yield completion
    
    def _fuzzy_match(self, candidate: str, query: str) -> bool:
        if not query:
            return True
            
        candidate_lower = candidate.lower()
        query_lower = query.lower()
        
        candidate_idx = 0
        for char in query_lower:
            while candidate_idx < len(candidate_lower) and candidate_lower[candidate_idx] != char:
                candidate_idx += 1
            if candidate_idx >= len(candidate_lower):
                return False
            candidate_idx += 1
        
        return True

    def _load_all_commands(self, base_commands: List[str]) -> List[str]:
        commands = set(base_commands)

        for directory in os.get_exec_path():
            if not directory:
                continue
            try:
                for entry in os.scandir(directory):
                    if not entry.name or entry.name in commands:
                        continue
                    try:
                        if entry.is_file() and os.access(entry.path, os.X_OK):
                            commands.add(entry.name)
                    except OSError:
                        continue
            except OSError:
                continue

        return sorted(commands)


class BashCompletionRunner:
    _OPTIONS_WITH_VALUES = {
        '-o', '-A', '-G', '-W', '-X', '-P', '-S', '-D', '-E', '-I', '-M', '-O', '-Q', '-R', '-T', '-U'
    }
    def __init__(self) -> None:
        self.available_scripts = [path for path in Config.BASH_COMPLETION_FILES if os.path.exists(path)]
        self.completion_dirs = [path for path in Config.BASH_COMPLETION_DIRS if os.path.isdir(path)]
        self._completion_map: Optional[Dict[str, Dict[str, str]]] = None
        self._attempted_commands: Set[str] = set()

    def get_completions(self, line: str, cursor_pos: int):
        if not self.available_scripts:
            return []

        command_name = self._extract_command_name(line)
        if not command_name:
            return []

        self._prepare_for_command(command_name)

        if command_name not in (self._completion_map or {}):
            return []

        comp_entry = self._completion_map[command_name]
        run_script = comp_entry.get('function')
        if not run_script:
            return []

        source_path = comp_entry.get('source')

        try:
            cmd = self._build_command(line, cursor_pos, command_name, run_script, source_path)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode != 0:
                return []

            token_length = self._current_token_length(line, cursor_pos)
            completions = []
            for item in result.stdout.splitlines():
                item = item.strip()
                if item:
                    completions.append(Completion(item, start_position=-token_length))
            return completions
        except Exception:
            return []

    def _ensure_completion_map(self) -> None:
        if self._completion_map is not None:
            return

        self._completion_map = {}
        script_sources = self._build_source_prefix()
        if not script_sources:
            return

        command = ['bash', '-lc', f'{script_sources} complete -p']
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            if result.returncode != 0:
                return

            self._parse_complete_output(result.stdout)
        except Exception:
            self._completion_map = {}

    def _prepare_for_command(self, command_name: str) -> None:
        self._ensure_completion_map()

        if self._completion_map and command_name in self._completion_map:
            return

        if command_name in self._attempted_commands:
            return

        self._attempted_commands.add(command_name)

        script_path = self._find_completion_file(command_name)
        if not script_path:
            return

        script_sources = f"{self._build_source_prefix()}source {shlex.quote(script_path)};"
        command = ['bash', '-lc', f'{script_sources} complete -p {shlex.quote(command_name)}']
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            if result.returncode != 0:
                return

            self._parse_complete_output(result.stdout, source_hint=script_path)
        except Exception:
            return

    def _parse_complete_output(self, output: str, source_hint: Optional[str] = None) -> None:
        if self._completion_map is None:
            self._completion_map = {}

        for line in output.splitlines():
            line = line.strip()
            if not line.startswith("complete "):
                continue

            parts = shlex.split(line)
            function_name = None
            commands: List[str] = []

            i = 1
            while i < len(parts):
                token = parts[i]
                if token in {"-F", "-C"} and (i + 1) < len(parts):
                    function_name = parts[i + 1]
                    i += 2
                elif token.startswith("-"):
                    i += 1
                    if (
                        token in self._OPTIONS_WITH_VALUES
                        and i < len(parts)
                        and not parts[i].startswith("-")
                    ):
                        i += 1
                else:
                    commands = parts[i:]
                    break

            if not function_name or not commands:
                continue

            for cmd in commands:
                entry = self._completion_map.get(cmd, {})
                entry['function'] = function_name
                if source_hint:
                    entry['source'] = source_hint
                self._completion_map[cmd] = entry

    def _find_completion_file(self, command_name: str) -> Optional[str]:
        if not self.completion_dirs:
            return None

        candidates = [command_name]
        if '-' in command_name:
            candidates.append(command_name.replace('-', '_'))

        for directory in self.completion_dirs:
            for candidate in candidates:
                path = os.path.join(directory, candidate)
                if os.path.isfile(path):
                    return path

            glob_pattern = os.path.join(directory, f"{command_name}.*")
            for path in glob.glob(glob_pattern):
                if os.path.isfile(path):
                    return path

        return None

    def _build_command(self, line: str, cursor_pos: int, command_name: str, function_name: str, source_path: Optional[str]) -> List[str]:
        script_sources = self._build_source_prefix()
        if source_path:
            script_sources += f"source {shlex.quote(source_path)};"

        line_before_cursor = line[:cursor_pos]
        words = self._split_words(line_before_cursor)
        if not words:
            words = [command_name]

        comp_words = " ".join(shlex.quote(word) for word in words)
        comp_cword = len(words) - 1

        script_body = (
            f"{script_sources}"
            f"COMP_LINE={shlex.quote(line)};"
            f"COMP_POINT={cursor_pos};"
            f"COMP_WORDS=({comp_words});"
            f"COMP_CWORD={comp_cword};"
            "COMPREPLY=();"
            f"{function_name} {shlex.quote(command_name)} >/dev/null;"
            "printf '%s\\n' \"${COMPREPLY[@]}\""
        )
        return ['bash', '-lc', script_body]

    def _current_token_length(self, line: str, cursor_pos: int) -> int:
        prefix = line[:cursor_pos]
        if not prefix or prefix.endswith(' '):
            return 0
        return len(prefix.split()[-1])

    def _build_source_prefix(self) -> str:
        return "".join([f"source {shlex.quote(path)};" for path in self.available_scripts])

    def _extract_command_name(self, line: str) -> Optional[str]:
        stripped = line.lstrip()
        if not stripped:
            return None
        return stripped.split()[0]

    def _split_words(self, text: str) -> List[str]:
        if not text:
            return []

        lexer = shlex.shlex(text, posix=True)
        lexer.whitespace_split = True
        words = list(lexer)

        if text and text[-1].isspace():
            words.append("")

        return words

class CompletionManager:
    def __init__(self):
        self.path_completer = DynamicPathCompleter()
        
    def get_completer(self):
        return self.path_completer
        
    def update_cache(self, path: str = None):
        if path is None:
            path = os.getcwd()
        
        cache_key = self.path_completer.scanner._get_cache_key(path)
        if cache_key in self.path_completer.scanner._cache:
            del self.path_completer.scanner._cache[cache_key]
            
        self.path_completer.scanner.metadata.clear_cache()
            
    def clear_cache(self):
        self.path_completer.scanner._cache.clear()
        self.path_completer.scanner._cache_time.clear()
        self.path_completer.scanner.metadata.clear_cache()
    
    def refresh_directory(self, path: str = None):
        self.update_cache(path)
        
    def set_show_hidden(self, show_hidden: bool):
        pass


def create_completion_manager() -> CompletionManager:
    return CompletionManager()


def get_file_metadata(file_path: str) -> str:
    metadata = FileMetadata()
    return metadata.get_file_info(file_path)
