# mdaviz Structure Improvements & Next Steps Plan

## Executive Summary

This document outlines a comprehensive plan for structural improvements to the mdaviz package. Based on architectural analysis and performance optimizations completed, we now focus on resolving coupling issues, implementing better separation of concerns, and preparing for future extensibility.

## Current State Assessment

### ✅ Performance Optimizations Completed (4,960 lines optimized)
- **LazyFolderScanner**: Parallel processing, batch operations, memory management
- **DataCache**: LRU eviction, memory monitoring, adaptive sizing
- **ChartView**: Memory-optimized plotting, lazy rendering, dual backends
- **Utils**: Async file loading, parallel processing, optimized file reading
- **MDAFile**: Enhanced caching, preloading, performance tracking
- **FitManager**: Async fitting, performance monitoring, thread safety
- **UserSettings**: Validation, backup/restore, error handling

### 📊 Codebase Metrics
- **Total Python Code**: 11,720 lines
- **Total Test Code**: 7,299 lines (62% test-to-code ratio)
- **Test Coverage**: 46% (target: 80%+)
- **Core Modules**: 25 Python files in src/mdaviz/

### 🔍 Architectural Analysis Results

#### Dependency Coupling Issues
```
High Coupling Modules (>5 dependencies):
├── MainWindow: 9 internal dependencies  ⚠️ CRITICAL
├── AboutDialog: 9 internal dependencies ⚠️ REFACTOR NEEDED
├── MDA_Folder: 8 internal dependencies ⚠️ HIGH
├── MDAFileTableView: 7 internal dependencies ⚠️ HIGH
└── MDAFileViz: 6 internal dependencies ⚠️ MODERATE
```

#### Circular Dependencies Identified
```
⚠️ Critical Issues:
├── mda_file ↔ mda_file_table_view
└── mda_folder ↔ mda_folder_table_view
```

#### Central Hub Dependencies
```
Over-used modules (dependency bottlenecks):
├── mdaviz.__init__: used by 20 modules
├── user_settings: used by 6 modules  
├── utils: used by 5 modules
└── mda_file_table_model: used by 5 modules
```

## Structural Improvement Roadmap

### Phase 1: Foundation Cleanup (Weeks 1-2)

#### 1.1 Resolve Circular Dependencies (Priority: CRITICAL)
**Problem**: Circular imports create fragile architecture and testing difficulties.

**Solutions**:
```python
# Current Issue: mda_file imports mda_file_table_view, which imports mda_file

# Solution A: Extract shared interfaces
# src/mdaviz/interfaces/file_interfaces.py
from abc import ABC, abstractmethod
from typing import Protocol

class FileDataProvider(Protocol):
    def get_file_data(self, file_path: str) -> dict: ...
    
class FileDisplayHandler(Protocol):
    def update_display(self, data: dict) -> None: ...

# Solution B: Use dependency injection
# src/mdaviz/services/file_service.py
class FileService:
    def __init__(self, data_provider, display_handler):
        self._data_provider = data_provider
        self._display_handler = display_handler
```

#### 1.2 Extract Configuration Management
**Problem**: Settings and constants scattered across modules.

**Solution**: Create dedicated configuration layer.
```python
# src/mdaviz/config/
├── __init__.py
├── app_config.py      # Application-wide settings
├── ui_config.py       # UI-specific configuration  
├── performance_config.py  # Performance tuning
└── defaults.py        # Default values and constants
```

#### 1.3 Implement Service Layer Architecture
**Problem**: Business logic mixed with UI components.

**Solution**: Extract services for core functionality.
```python
# src/mdaviz/services/
├── __init__.py
├── file_service.py        # File operations
├── data_service.py        # Data processing
├── visualization_service.py  # Plotting logic
├── cache_service.py       # Caching operations
└── settings_service.py    # Settings management
```

### Phase 2: Architectural Refactoring (Weeks 3-4)

#### 2.1 Implement Dependency Injection Container
**Goal**: Reduce tight coupling between modules.

```python
# src/mdaviz/core/container.py
from typing import Dict, Type, Any, TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')

class ServiceContainer:
    """Dependency injection container for managing services."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance."""
        self._services[service_type.__name__] = instance
    
    def register_factory(self, service_type: Type[T], factory: callable) -> None:
        """Register a service factory."""
        self._factories[service_type.__name__] = factory
    
    def get(self, service_type: Type[T]) -> T:
        """Get service instance."""
        name = service_type.__name__
        if name in self._services:
            return self._services[name]
        elif name in self._factories:
            instance = self._factories[name]()
            self._services[name] = instance
            return instance
        else:
            raise ValueError(f"Service {name} not registered")

# Usage in main application
container = ServiceContainer()
container.register(FileService, FileService(cache_service, config))
```

#### 2.2 Implement Event Bus Pattern
**Goal**: Replace direct signal connections with centralized event system.

```python
# src/mdaviz/core/event_bus.py
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    FILE_SELECTED = "file_selected"
    FILE_LOADED = "file_loaded"
    PLOT_UPDATED = "plot_updated"
    CACHE_UPDATED = "cache_updated"
    SETTINGS_CHANGED = "settings_changed"

@dataclass
class Event:
    type: EventType
    data: Any
    source: str

class EventBus:
    """Centralized event management system."""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")

# Usage
event_bus = EventBus()
event_bus.subscribe(EventType.FILE_SELECTED, lambda e: print(f"File selected: {e.data}"))
```

#### 2.3 Create Application Services Layer
**Goal**: Separate business logic from UI components.

```python
# src/mdaviz/services/application_service.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class ApplicationService(ABC):
    """Base class for application services."""
    
    def __init__(self, container: ServiceContainer, event_bus: EventBus):
        self.container = container
        self.event_bus = event_bus

class FileManagementService(ApplicationService):
    """Service for file operations and management."""
    
    async def load_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load file with caching and error handling."""
        try:
            # Use cache service
            cache_service = self.container.get(CacheService)
            cached_data = cache_service.get(file_path)
            
            if cached_data:
                self.event_bus.publish(Event(EventType.FILE_LOADED, cached_data, "cache"))
                return cached_data
            
            # Load from disk
            data = await self._load_from_disk(file_path)
            cache_service.set(file_path, data)
            
            self.event_bus.publish(Event(EventType.FILE_LOADED, data, "disk"))
            return data
            
        except Exception as e:
            self.event_bus.publish(Event(EventType.ERROR, str(e), "file_service"))
            return None

class VisualizationService(ApplicationService):
    """Service for data visualization operations."""
    
    def update_plot(self, data: Dict[str, Any], style: Dict[str, Any]) -> bool:
        """Update plot with new data and styling."""
        try:
            # Process data
            processed_data = self._process_plot_data(data)
            
            # Get chart view service
            chart_service = self.container.get(ChartService)
            success = chart_service.render(processed_data, style)
            
            if success:
                self.event_bus.publish(Event(EventType.PLOT_UPDATED, processed_data, "viz_service"))
            
            return success
            
        except Exception as e:
            self.event_bus.publish(Event(EventType.ERROR, str(e), "viz_service"))
            return False
```

### Phase 3: Advanced Architecture Patterns (Weeks 5-6)

#### 3.1 Implement Repository Pattern for Data Access
**Goal**: Abstract data access and improve testability.

```python
# src/mdaviz/repositories/
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class FileRepository(ABC):
    """Abstract repository for file operations."""
    
    @abstractmethod
    async def get_file_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_files_in_directory(self, directory: str) -> List[str]:
        pass
    
    @abstractmethod
    async def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        pass

class MDAFileRepository(FileRepository):
    """Concrete implementation for MDA file operations."""
    
    def __init__(self, cache_service: CacheService, file_reader: OptimizedFileReader):
        self.cache_service = cache_service
        self.file_reader = file_reader
    
    async def get_file_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        # Implementation with caching, error handling, etc.
        pass

# Usage in services
class FileManagementService(ApplicationService):
    def __init__(self, container: ServiceContainer, event_bus: EventBus):
        super().__init__(container, event_bus)
        self.file_repo = container.get(FileRepository)
    
    async def load_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        return await self.file_repo.get_file_data(file_path)
```

#### 3.2 Create Command Pattern for User Actions
**Goal**: Encapsulate user actions for undo/redo and better testing.

```python
# src/mdaviz/commands/
from abc import ABC, abstractmethod
from typing import Any, Optional

class Command(ABC):
    """Base command interface."""
    
    @abstractmethod
    def execute(self) -> Any:
        pass
    
    @abstractmethod
    def undo(self) -> Any:
        pass

class LoadFileCommand(Command):
    """Command to load a file."""
    
    def __init__(self, file_service: FileManagementService, file_path: str):
        self.file_service = file_service
        self.file_path = file_path
        self.previous_state = None
    
    async def execute(self) -> Any:
        self.previous_state = self.file_service.get_current_file()
        return await self.file_service.load_file(self.file_path)
    
    async def undo(self) -> Any:
        if self.previous_state:
            return await self.file_service.load_file(self.previous_state)

class CommandInvoker:
    """Manages command execution with undo/redo support."""
    
    def __init__(self):
        self.history: List[Command] = []
        self.current_index = -1
    
    async def execute_command(self, command: Command) -> Any:
        result = await command.execute()
        
        # Clear forward history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        self.history.append(command)
        self.current_index += 1
        return result
    
    async def undo(self) -> Any:
        if self.current_index >= 0:
            command = self.history[self.current_index]
            result = await command.undo()
            self.current_index -= 1
            return result
```

### Phase 4: MainWindow Refactoring (Weeks 7-8) 🎯 FINAL PHASE

#### 4.1 Extract MainWindow Responsibilities
**Current Problems**:
- 9 internal dependencies (too high)
- Mixed responsibilities (UI, business logic, state management)
- 600+ lines (complex initialization)
- Low test coverage (46%)

**Refactoring Strategy**:
```python
# Break MainWindow into focused components:

# src/mdaviz/ui/
├── main_window.py          # Pure UI logic
├── window_manager.py       # Window state, geometry, settings
├── menu_manager.py         # Menu and toolbar management
├── status_manager.py       # Status bar and notifications
└── layout_manager.py       # Layout and splitter management

# src/mdaviz/controllers/
├── application_controller.py  # Main application coordination
├── file_controller.py        # File operations coordination
├── view_controller.py        # View state management
└── settings_controller.py    # Settings coordination

# Simplified MainWindow
class MainWindow(QMainWindow):
    """Simplified main window focused on UI concerns only."""
    
    def __init__(self, application_controller: ApplicationController):
        super().__init__()
        self.app_controller = application_controller
        
        # Delegate complex initialization
        self.window_manager = WindowManager(self)
        self.menu_manager = MenuManager(self)
        self.status_manager = StatusManager(self)
        self.layout_manager = LayoutManager(self)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up UI components only."""
        self.window_manager.setup_window_properties()
        self.menu_manager.setup_menus()
        self.layout_manager.setup_layout()
        self.status_manager.setup_status_bar()
    
    def _connect_signals(self) -> None:
        """Connect UI signals to controller."""
        # Delegate all business logic to controllers
        pass
```

#### 4.2 Implement Clean Architecture Patterns
```python
# Final architecture after refactoring:

src/mdaviz/
├── core/                   # Core abstractions
│   ├── container.py        # Dependency injection
│   ├── event_bus.py        # Event system
│   └── interfaces.py       # Abstract interfaces
├── services/               # Business logic layer
│   ├── file_service.py     # File operations
│   ├── data_service.py     # Data processing
│   ├── visualization_service.py  # Plotting
│   └── cache_service.py    # Caching
├── repositories/           # Data access layer
│   ├── file_repository.py  # File data access
│   └── settings_repository.py  # Settings access
├── controllers/            # Application coordination
│   ├── application_controller.py
│   ├── file_controller.py
│   └── view_controller.py
├── ui/                     # Pure UI components
│   ├── main_window.py      # Main window UI
│   ├── dialogs/           # Dialog components
│   └── widgets/           # Custom widgets
├── models/                 # Data models
│   ├── file_model.py      # File data models
│   └── plot_model.py      # Plot data models
└── config/                 # Configuration
    ├── app_config.py      # App settings
    └── defaults.py        # Default values
```

### Phase 5: Testing & Quality Assurance (Weeks 9-10)

#### 5.1 Comprehensive Integration Testing
```python
# tests/integration/
├── test_file_loading_flow.py     # End-to-end file loading
├── test_visualization_flow.py    # Plotting workflow
├── test_settings_flow.py         # Settings management
└── test_performance_flow.py      # Performance validation

# Example integration test
class TestFileLoadingFlow:
    async def test_complete_file_loading_workflow(self):
        """Test complete file loading from UI to visualization."""
        # Setup services with test doubles
        container = create_test_container()
        event_bus = EventBus()
        
        # Test the complete flow
        app_controller = ApplicationController(container, event_bus)
        
        # Simulate user actions
        result = await app_controller.load_file("test.mda")
        
        # Verify all components worked together
        assert result is not None
        assert event_bus.has_event(EventType.FILE_LOADED)
        assert container.get(CacheService).has_cached("test.mda")
```

#### 5.2 Performance Regression Testing
```python
# tests/performance/
├── test_memory_usage.py          # Memory leak detection
├── test_loading_performance.py   # File loading benchmarks
├── test_visualization_performance.py  # Plotting performance
└── test_concurrent_operations.py # Thread safety validation

@pytest.mark.benchmark
class TestPerformanceRegression:
    def test_file_loading_performance(self, benchmark):
        """Ensure file loading performance doesn't regress."""
        def load_test_file():
            return load_mda_file("large_test_file.mda")
        
        result = benchmark(load_test_file)
        assert result is not None
        
        # Performance thresholds
        assert benchmark.stats['mean'] < 2.0  # < 2 seconds
        assert get_memory_usage() < 100  # < 100MB
```

## Implementation Timeline

### Week 1-2: Foundation Cleanup
- [x] Performance optimizations (COMPLETED)
- [ ] Resolve circular dependencies (arch-01)
- [ ] Extract configuration management (arch-06)
- [ ] Create service layer structure (arch-04)

### Week 3-4: Architectural Refactoring  
- [ ] Implement dependency injection (arch-03)
- [ ] Create event bus system (arch-05)
- [ ] Implement application services (arch-04)
- [ ] Add separation of concerns (arch-07)

### Week 5-6: Advanced Patterns
- [ ] Repository pattern implementation
- [ ] Command pattern for user actions
- [ ] Plugin architecture foundation (arch-10)

### Week 7-8: MainWindow Refactoring (FINAL)
- [ ] Extract MainWindow responsibilities (arch-02)
- [ ] Reduce coupling to <3 dependencies (arch-02)
- [ ] Implement clean architecture (arch-09)
- [ ] Achieve 60%+ test coverage for MainWindow

### Week 9-10: Testing & QA
- [ ] Comprehensive integration tests (arch-08)
- [ ] Performance regression testing
- [ ] Documentation updates
- [ ] User acceptance testing

## Success Metrics

### Structural Quality Metrics
- **Coupling Reduction**: MainWindow dependencies: 9 → <3
- **Circular Dependencies**: 2 → 0
- **Test Coverage**: 46% → 80%+
- **Module Complexity**: Reduce average cyclomatic complexity by 40%

### Performance Metrics
- **Memory Usage**: <100MB for typical operations
- **File Loading**: <2 seconds for large files
- **UI Responsiveness**: <50ms for common operations
- **Test Execution**: <30 seconds for full test suite

### Maintainability Metrics
- **Documentation Coverage**: 100% public APIs documented
- **Code Review Time**: <30 minutes average
- **New Feature Development**: 50% faster due to better architecture
- **Bug Fix Time**: 60% reduction in average fix time

## Risk Assessment

### High Risk Items
1. **Breaking Changes**: Refactoring may break existing functionality
   - **Mitigation**: Comprehensive test suite, feature flags, gradual migration
2. **Performance Regression**: New architecture may impact performance
   - **Mitigation**: Continuous benchmarking, performance budgets
3. **Team Learning Curve**: New patterns require team training
   - **Mitigation**: Documentation, pair programming, gradual introduction

### Medium Risk Items
1. **Test Suite Maintenance**: More complex testing infrastructure
2. **Increased Initial Complexity**: More files and abstractions
3. **Migration Effort**: Significant refactoring required

## Conclusion

This comprehensive plan transforms mdaviz from a well-functioning but tightly-coupled application into a maintainable, extensible, and testable architecture. The phased approach ensures minimal risk while delivering maximum architectural benefits.

**Key Benefits**:
- **Maintainability**: Easier to modify and extend
- **Testability**: Better separation enables thorough testing  
- **Performance**: Continued optimizations with better structure
- **Extensibility**: Plugin architecture for future enhancements
- **Team Productivity**: Cleaner code accelerates development

**Next Step**: Begin Phase 1 with circular dependency resolution, as this is critical for all subsequent architectural improvements. 